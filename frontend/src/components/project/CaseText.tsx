/**
 * Renders case-study text the way authors write it: blank lines separate
 * blocks, and runs of "•" / "-" lines become real lists. Mixed blocks (a plain
 * line followed by bullets) are split accordingly, otherwise the whole section
 * collapses into one dense run of text.
 *
 * `linesAsList` is for fields documented as "one item per line" (Функции):
 * there the author is told every line becomes a bullet, so plain lines must
 * become list items too instead of being glued into one paragraph.
 *
 * Shared by the public case page and the in-editor preview so what an author
 * sees while writing matches what visitors get.
 */
export function CaseText({
  text,
  linesAsList = false,
}: {
  text: string;
  linesAsList?: boolean;
}) {
  const isBullet = (line: string) => /^[-•*]\s+/.test(line);

  const blocks = text.split(/\n\s*\n/).filter((b) => b.trim());

  return (
    <>
      {blocks.map((block, i) => {
        const lines = block
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean);

        // Pre-group each line as either a bullet or a paragraph so a run of
        // bullets becomes exactly one <ul>, even inside a mixed block.
        const groups: Array<{ bullet: boolean; items: string[] }> = [];
        for (const line of lines) {
          // In "one item per line" fields every line is a list item, so a
          // stray "•" must not split the run into two lists.
          const bullet = linesAsList || isBullet(line);
          const last = groups[groups.length - 1];
          if (last && last.bullet === bullet) last.items.push(line);
          else groups.push({ bullet, items: [line] });
        }

        return (
          <div key={i} className="case-text-block">
            {groups.map((group, j) =>
              group.bullet ? (
                <ul key={j}>
                  {group.items.map((item, k) => (
                    <li key={k}>{item.replace(/^[-•*]\s+/, "")}</li>
                  ))}
                </ul>
              ) : (
                <p key={j}>{group.items.join(" ")}</p>
              ),
            )}
          </div>
        );
      })}
    </>
  );
}
