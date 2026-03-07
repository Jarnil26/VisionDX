"use client";

import React from "react";

interface SafeMarkdownProps {
  content: string;
}

/**
 * A lightweight, safe Markdown renderer for the VisionDX Chat.
 * Handles:
 * - ### Header 3
 * - #### Header 4 
 * - **Bold**
 * - • Bullet points
 * - \n Newlines
 */
export const SafeMarkdown: React.FC<SafeMarkdownProps> = ({ content }) => {
  if (!content) return null;

  // Split by double newlines for paragraphs
  const paragraphs = content.split(/\n\n+/);

  return (
    <div className="space-y-4">
      {paragraphs.map((para, i) => {
        // Handle Headers
        if (para.startsWith("### ")) {
          return (
            <h3 key={i} className="text-base font-black text-slate-900 flex items-center gap-2 mt-4 first:mt-0">
              {para.replace("### ", "")}
            </h3>
          );
        }
        if (para.startsWith("#### ")) {
          return (
            <h4 key={i} className="text-sm font-black text-slate-800 flex items-center gap-2 mt-2">
              {para.replace("#### ", "")}
            </h4>
          );
        }

        // Handle Bullet Points
        if (para.includes("\n• ") || para.startsWith("• ")) {
          const lines = para.split("\n");
          return (
            <ul key={i} className="space-y-2 ml-1">
              {lines.map((line, j) => {
                const cleanLine = line.replace(/^•\s*/, "").trim();
                if (!cleanLine) return null;
                return (
                  <li key={j} className="flex gap-2 text-sm text-slate-600 leading-relaxed">
                    <span className="text-blue-500 shrink-0">•</span>
                    <span>{renderBold(cleanLine)}</span>
                  </li>
                );
              })}
            </ul>
          );
        }

        // Regular Paragraph
        return (
          <p key={i} className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
            {renderBold(para)}
          </p>
        );
      })}
    </div>
  );
};

/**
 * Helper to render **bold** text within a string
 */
function renderBold(text: string) {
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-black text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return part;
  });
}
