import {Fragment} from 'react'
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";

function AiResponseMarkdown({message}) {
  return (
    <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      code({ node, inline, className, children, ...props }) {
        return !inline ? (
          <SyntaxHighlighter
            style={dracula}
            language="javascript" // Default, change dynamically if needed
            PreTag="div"
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        ) : (
          <code className="bg-gray-700 text-white p-1 rounded" {...props}>
            {children}
          </code>
        );
      },
      h1: ({ children }) => <h1 className="text-xl font-bold mt-2">{children}</h1>,
      h2: ({ children }) => <h2 className="text-lg font-semibold mt-2">{children}</h2>,
      h3: ({ children }) => <h3 className="text-md font-semibold mt-2">{children}</h3>,
      p: ({ children }) => <p className="text-gray-300">{children}</p>,
      ul: ({ children }) => <ul className="list-disc ml-4">{children}</ul>,
      ol: ({ children }) => <ol className="list-decimal ml-4">{children}</ol>,
      blockquote: ({ children }) => (
        <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-400">
          {children}
        </blockquote>
      ),
    }}
  >
    {message}
  </ReactMarkdown>
  )
}

export default AiResponseMarkdown