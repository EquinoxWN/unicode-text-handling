package portfolio.unicodetexthandling;

import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/** Mojibake: UTF-8 bytes decoded as Windows-1252, and how to undo it. */
public final class Mojibake {
    /** Default number of mis-decodings to undo. */
    public static final int MAX_ROUNDS = 3;

    /** Windows-1252 bytes 0x80..0x9F (WHATWG); undefined bytes map to the C1 control of the same value. */
    private static final String HIGH = "€\u0081‚ƒ„…†‡ˆ‰Š‹"
            + "Œ\u008dŽ\u008f\u0090‘’“”•–—˜™š›"
            + "œ\u009džŸ";

    private static final char[] DECODE = new char[256];
    private static final Map<Character, Integer> ENCODE = new HashMap<>();

    static {
        for (int b = 0; b < 256; b++) {
            DECODE[b] = b >= 0x80 && b < 0xA0 ? HIGH.charAt(b - 0x80) : (char) b;
            ENCODE.put(DECODE[b], b);
        }
    }

    private Mojibake() {}

    /** Repaired text and how many mis-decodings were undone. */
    public record Repair(String text, int rounds) {}

    /** The Windows-1252 character for a byte value. */
    static char decodeByte(int b) {
        return DECODE[b & 0xFF];
    }

    /** Encode as UTF-8 and decode as Windows-1252: what a mis-configured reader shows. */
    public static String garble(String text) {
        Graphemes.check(text);
        if (!isWellFormed(text)) {
            throw new IllegalArgumentException("lone surrogate: not well-formed text");
        }
        StringBuilder sb = new StringBuilder();
        for (byte b : text.getBytes(StandardCharsets.UTF_8)) {
            sb.append(DECODE[b & 0xFF]);
        }
        return sb.toString();
    }

    /** True when text has no unpaired surrogates. */
    static boolean isWellFormed(String text) {
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (Character.isHighSurrogate(c) && i + 1 < text.length() && Character.isLowSurrogate(text.charAt(i + 1))) {
                i++;
            } else if (Character.isSurrogate(c)) {
                return false;
            }
        }
        return true;
    }

    /** Undo one round, or empty if text is not Windows-1252-encodable valid UTF-8. */
    public static Optional<String> unwindOnce(String text) {
        byte[] bytes = new byte[text.length()];
        for (int i = 0; i < text.length(); i++) {
            Integer b = ENCODE.get(text.charAt(i));
            if (b == null) {
                return Optional.empty();
            }
            bytes[i] = (byte) b.intValue();
        }
        try {
            return Optional.of(StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes))
                    .toString());
        } catch (CharacterCodingException e) {
            return Optional.empty(); // not UTF-8 underneath: this text is not mojibake
        }
    }

    /** Undo up to maxRounds of UTF-8-read-as-Windows-1252, stopping when a round would not apply. */
    public static Repair repair(String text, int maxRounds) {
        Graphemes.check(text);
        if (maxRounds < 0 || maxRounds > 10) {
            throw new IllegalArgumentException("maxRounds must be between 0 and 10");
        }
        int rounds = 0;
        while (rounds < maxRounds) {
            Optional<String> fixed = unwindOnce(text);
            if (fixed.isEmpty() || fixed.get().equals(text)) {
                break;
            }
            text = fixed.get();
            rounds++;
        }
        return new Repair(text, rounds);
    }

    /** Repair with the default round limit. */
    public static Repair repair(String text) {
        return repair(text, MAX_ROUNDS);
    }
}
