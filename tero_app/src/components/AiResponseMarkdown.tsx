import React, { Fragment, useLayoutEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check } from "lucide-react";
import type { Components } from "react-markdown";

interface AiResponseMarkdownProps {
  message: string;
  // kept for compatibility if callers still pass it; not used here
  isStreaming?: boolean;
}

export default function AiResponseMarkdown({
  message,
  isStreaming,
}: AiResponseMarkdownProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Typing effect state
  const [displayedMessage, setDisplayedMessage] = useState<string>("");
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  // const [totalLength, setTotalLength] = useState<number>(0);

  useLayoutEffect(() => {
    if (isStreaming)
      if (currentIndex < message.length) {
        const timeout = setTimeout(() => {
          setDisplayedMessage((prev) => prev + message[currentIndex]);
          setCurrentIndex((prev) => prev + 1);
        }, 0.4 + Math.random() * 5); // Varying speed for more natural effect

        return () => clearTimeout(timeout);
      }
  }, [currentIndex]);

  const handleCopyCode = (code: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(code).catch(() => {});
    }
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  type MarkdownCodeProps = React.ComponentPropsWithoutRef<"code"> & {
    inline?: boolean;
    node?: unknown;
    className?: string;
    children?: React.ReactNode;
  };

  const CodeBlock = ({
    node: _node,
    inline,
    className,
    children,
    ...props
  }: MarkdownCodeProps) => {
    const code = String(children ?? "").replace(/\n$/, "");
    const match = /language-(\w+)/.exec(className ?? "");
    const language = match ? match[1] : "text";

    const isInline = inline ?? !code.includes("\n");

    if (isInline) {
      return (
        <code
          className="bg-text/10 text-text px-1.5 py-0.5 rounded font-mono text-sm border border-text/5"
          {...props}
        >
          {children as React.ReactNode}
        </code>
      );
    }

    return (
      <div className="relative group my-2">
        <button
          onClick={() => handleCopyCode(code)}
          className="absolute right-2 top-2 p-2 rounded bg-background/40 transition-colors z-10"
          title="Copy code"
        >
          {copiedCode === code ? (
            <Check className="w-4 h-4 text-success" />
          ) : (
            <Copy className="w-4 h-4 text-text/60 group-hover:text-text" />
          )}
        </button>
        <SyntaxHighlighter
          style={atomDark as any}
          language={language}
          PreTag="div"
          className="!mt-0 dark:bg-text/5 bg-text/80 rounded-lg no-scrollbar"
          showLineNumbers
          wrapLongLines
          {...(props as any)}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    );
  };

  const sharedComponents = {
    code: ({ node, inline, className, children, ...props }: any) => (
      <CodeBlock node={node} inline={inline} className={className} {...props}>
        {children}
      </CodeBlock>
    ),
    h1: ({ node, children, ...props }: any) => (
      <h1 className="text-3xl font-bold mt-8 mb-6 text-title" {...props}>
        {children}
      </h1>
    ),
    h2: ({ node, children, ...props }: any) => (
      <h2 className="text-2xl font-semibold mt-6 mb-4 text-title/90" {...props}>
        {children}
      </h2>
    ),
    h3: ({ node, children, ...props }: any) => (
      <h3 className="text-xl font-semibold mt-5 mb-3 text-title/80" {...props}>
        {children}
      </h3>
    ),
    p: ({ node, children, ...props }: any) => (
      <p className="text-text leading-relaxed mb-2 text-[15px]" {...props}>
        {children}
      </p>
    ),
    ul: ({ node, children, ...props }: any) => (
      <ul
        className="list-disc ml-6 my-4 text-text space-y-2 marker:text-title"
        {...props}
      >
        {children}
      </ul>
    ),
    ol: ({ node, children, ...props }: any) => (
      <ol
        className="list-decimal ml-6 my-4 text-text/80 space-y-2 marker:text-title"
        {...props}
      >
        {children}
      </ol>
    ),
    li: ({ node, children, ...props }: any) => (
      <li className="text-text/80 pl-2" {...props}>
        {children}
      </li>
    ),
    blockquote: ({ node, children, ...props }: any) => (
      <blockquote
        className="relative my-6 pl-6 pr-4 py-4 border-l-2 border-text/40 bg-gradient-to-r from-text/10 to-transparent rounded-r-lg"
        {...props}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/3 to-transparent rounded-r-lg" />
        <div className="relative text-text italic">{children}</div>
      </blockquote>
    ),
    a: ({ node, children, ...props }: any) => (
      <a
        href={props.href ?? ""}
        className="text-cyan-400 hover:text-cyan-300 underline decoration-cyan-800 hover:decoration-cyan-600 transition-colors"
        target="_blank"
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
    strong: ({ node, children, ...props }: any) => (
      <strong {...props}>{children}</strong>
    ),
    em: ({ node, children, ...props }: any) => <em {...props}>{children}</em>,
    del: ({ node, children, ...props }: any) => (
      <del {...props}>{children}</del>
    ),
    table: ({ node, children, ...props }: any) => (
      <div
        className="my-6 overflow-x-auto rounded-lg border border-text/20 bg-text/20 no-scrollbar"
        {...props}
      >
        <table className="min-w-full divide-y divide-text/30">{children}</table>
      </div>
    ),
    thead: ({ node, children, ...props }: any) => (
      <thead className="bg-text/20" {...props}>
        {children}
      </thead>
    ),
    tbody: ({ node, children, ...props }: any) => (
      <tbody className="divide-y divide-text/30" {...props}>
        {children}
      </tbody>
    ),
    tr: ({ node, children, ...props }: any) => (
      <tr className="transition-colors hover:divide-text/30" {...props}>
        {children}
      </tr>
    ),
    th: ({ node, children, ...props }: any) => (
      <th
        className="px-6 py-4 text-left text-sm font-semibold text-text"
        {...props}
      >
        {children}
      </th>
    ),
    td: ({ node, children, ...props }: any) => (
      <td
        className="px-6 py-4 text-sm text-text/80 whitespace-nowrap"
        {...props}
      >
        {children}
      </td>
    ),
    hr: ({ node, ...props }: any) => <hr className="my-2.5" {...props} />,
    img: ({ node, ...props }: any) => (
      <img
        src={props.src ?? ""}
        alt={props.alt ?? ""}
        className="p-1 max-h-96 max-w-full aspect-auto h-auto rounded-md cursor-pointer"
        onClick={() =>
          props.src &&
          typeof window !== "undefined" &&
          window.open(props.src, "_blank")
        }
      />
    ),
  } as const;

  return (
    <Fragment>
      <div className="relative ">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={sharedComponents as Components}
        >
          {isStreaming ? displayedMessage : message}
        </ReactMarkdown>
      </div>
    </Fragment>
  );
}
