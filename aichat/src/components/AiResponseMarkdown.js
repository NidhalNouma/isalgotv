import { Fragment, useState } from 'react';
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, Check } from 'lucide-react';

function AiResponseMarkdown({ message }) {
  const [copiedCode, setCopiedCode] = useState(null);

  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <Fragment>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }) {
            
            const code = String(children).replace(/\n$/, "");
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : 'text';

            const codeString = String(children).trim();
            const isInline = inline !== undefined ? inline : !codeString.includes("\n");

            if (isInline) {
                return (
                  <code className="bg-text/10 text-text px-1.5 py-0.5 rounded font-mono text-sm border border-text/5">
                    {children}
                  </code>
                );
            }

            return (
              <div className="relative group">
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
                <div className="relative">
                  {/* <div className="absolute inset-0 bg-gradient-to-r from-text/10 to-text/5 rounded-lg" /> */}
                  <SyntaxHighlighter
                    style={atomDark}
                    language={language}
                    PreTag="div"
                    className="!mt-0 dark:bg-text/5 bg-text/80 rounded-lg no-scrollbar"
                    showLineNumbers
                    wrapLongLines
                    {...props}
                  >
                    {code}
                  </SyntaxHighlighter>
                </div>
              </div>
            )
          },
          h1: ({ children }) => (
            <h1 className="text-3xl font-bold mt-8 mb-6 text-transparent bg-clip-text bg-gradient-to-r from-title to-text/80">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-2xl font-semibold mt-6 mb-4 text-transparent bg-clip-text bg-gradient-to-r from-title to-text/80">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xl font-semibold mt-5 mb-3 text-transparent bg-clip-text bg-gradient-to-r from-title to-text/80">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="text-text leading-relaxed mb-2 text-[15px]">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc ml-6 my-4 text-text space-y-2 marker:text-title">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal ml-6 my-4 text-text/80 space-y-2 marker:text-title">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-text/80 pl-2">{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote className="relative my-6 pl-6 pr-4 py-4 border-l-2 border-text/40 bg-gradient-to-r from-text/20 to-transparent rounded-r-lg">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/3 to-transparent rounded-r-lg" />
              <div className="relative text-text italic">
                {children}
              </div>
            </blockquote>
          ),
          a: ({ children, href }) => (
            <a 
              href={href}
              className="text-cyan-400 hover:text-cyan-300 underline decoration-cyan-800 hover:decoration-cyan-600 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
          table: ({ children }) => (
            <div className="my-6 overflow-x-auto rounded-lg border border-text/20 bg-text/20 no-scrollbar">
              <table className="min-w-full divide-y divide-text/30">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-text/20">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-text/30">{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="transition-colors hover:divide-text/30">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-6 py-4 text-left text-sm font-semibold text-text">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-6 py-4 text-sm text-text/80 whitespace-nowrap">{children}</td>
          ),
        }}
      >
        {message}
      </ReactMarkdown>
    </Fragment>
  );
}

export default AiResponseMarkdown;