export function AnswerBody({ text }: { text: string }) {
  const lines = text.split("\n")
  const hasList = lines.some((line) => /^\s*[-•]\s+/.test(line))
  if (!hasList) {
    return <p className="break-words whitespace-pre-wrap">{text}</p>
  }

  const blocks: Array<{ type: "text"; text: string } | { type: "list"; items: string[] }> = []
  let items: string[] = []

  const flush = () => {
    if (items.length === 0) return
    blocks.push({ type: "list", items })
    items = []
  }

  for (const line of lines) {
    const item = /^\s*[-•]\s+(.*)$/.exec(line)
    if (item) {
      items.push(item[1])
      continue
    }
    flush()
    if (line.trim()) blocks.push({ type: "text", text: line })
  }
  flush()

  return (
    <div className="space-y-2">
      {blocks.map((block, index) =>
        block.type === "list" ? (
          <ul key={index} className="list-disc space-y-1 pl-4">
            {block.items.map((item, itemIndex) => (
              <li key={`${index}-${itemIndex}`} className="break-words">
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p key={index} className="break-words">
            {block.text}
          </p>
        ),
      )}
    </div>
  )
}
