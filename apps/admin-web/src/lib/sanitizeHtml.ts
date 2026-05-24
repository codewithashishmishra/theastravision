'use client';

import DOMPurify from 'isomorphic-dompurify';

const ALLOWED_TAGS = [
  'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4',
  'table', 'thead', 'tbody', 'tr', 'th', 'td', 'span', 'motion', 'motion.div', 'div',
];

const ALLOWED_ATTR = ['href', 'target', 'rel', 'class', 'style'];

export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
  });
}
