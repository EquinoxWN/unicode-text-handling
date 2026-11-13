package portfolio.unicodetexthandling;

import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Encoding experiment: the four different 'lengths' of one string. */
public final class TextMeasure {
    private TextMeasure() {}

    /** UTF-8 bytes, UTF-16 code units, code points and grapheme clusters of a string. */
    public record Measurement(int utf8Bytes, int utf16Units, int codePoints, int graphemes) {}

    /** Measure text; lone surrogates are rejected instead of being silently replaced by '?'. */
    public static Measurement measure(String text) {
        Graphemes.check(text);
        int bytes;
        try {
            bytes = StandardCharsets.UTF_8.newEncoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .encode(CharBuffer.wrap(text))
                    .remaining();
        } catch (CharacterCodingException e) {
            throw new IllegalArgumentException("lone surrogate: not well-formed text", e);
        }
        return new Measurement(
                bytes,
                text.length(),
                text.codePointCount(0, text.length()),
                Graphemes.breakIterator(text).size());
    }
}
