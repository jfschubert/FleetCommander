// Icons from Lucide (https://lucide.dev), ISC license (Feather-derived icons: MIT) – see NOTICE.
import React from 'react';

const ICONS = {
  grid: [["rect", {"width": "7", "height": "7", "x": "3", "y": "3", "rx": "1"}], ["rect", {"width": "7", "height": "7", "x": "14", "y": "3", "rx": "1"}], ["rect", {"width": "7", "height": "7", "x": "14", "y": "14", "rx": "1"}], ["rect", {"width": "7", "height": "7", "x": "3", "y": "14", "rx": "1"}]],
  layers: [["path", {"d": "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"}], ["path", {"d": "M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"}], ["path", {"d": "M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"}]],
  wand: [["path", {"d": "m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72"}], ["path", {"d": "m14 7 3 3"}], ["path", {"d": "M5 6v4"}], ["path", {"d": "M19 14v4"}], ["path", {"d": "M10 2v2"}], ["path", {"d": "M7 8H3"}], ["path", {"d": "M21 16h-4"}], ["path", {"d": "M11 3H9"}]],
  zones: [["rect", {"width": "18", "height": "18", "x": "3", "y": "3", "rx": "2"}], ["path", {"d": "M3 9h18"}], ["path", {"d": "M9 21V9"}]],
  keyboard: [["path", {"d": "M10 8h.01"}], ["path", {"d": "M12 12h.01"}], ["path", {"d": "M14 8h.01"}], ["path", {"d": "M16 12h.01"}], ["path", {"d": "M18 8h.01"}], ["path", {"d": "M6 8h.01"}], ["path", {"d": "M7 16h10"}], ["path", {"d": "M8 12h.01"}], ["rect", {"width": "20", "height": "16", "x": "2", "y": "4", "rx": "2"}]],
  preview: [["path", {"d": "M21 9V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10c0 1.1.9 2 2 2h4"}], ["rect", {"width": "10", "height": "7", "x": "12", "y": "13", "rx": "2"}]],
  brush: [["path", {"d": "m14.622 17.897-10.68-2.913"}], ["path", {"d": "M18.376 2.622a1 1 0 1 1 3.002 3.002L17.36 9.643a.5.5 0 0 0 0 .707l.944.944a2.41 2.41 0 0 1 0 3.408l-.944.944a.5.5 0 0 1-.707 0L8.354 7.348a.5.5 0 0 1 0-.707l.944-.944a2.41 2.41 0 0 1 3.408 0l.944.944a.5.5 0 0 0 .707 0z"}], ["path", {"d": "M9 8c-1.804 2.71-3.97 3.46-6.583 3.948a.507.507 0 0 0-.302.819l7.32 8.883a1 1 0 0 0 1.185.204C12.735 20.405 16 16.792 16 15"}]],
  lock: [["rect", {"width": "18", "height": "11", "x": "3", "y": "11", "rx": "2", "ry": "2"}], ["path", {"d": "M7 11V7a5 5 0 0 1 10 0v4"}]],
  code: [["path", {"d": "m18 16 4-4-4-4"}], ["path", {"d": "m6 8-4 4 4 4"}], ["path", {"d": "m14.5 4-5 16"}]],
  shield: [["path", {"d": "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"}], ["path", {"d": "m9 12 2 2 4-4"}]],
  monitor: [["rect", {"width": "20", "height": "14", "x": "2", "y": "3", "rx": "2"}], ["line", {"x1": "8", "x2": "16", "y1": "21", "y2": "21"}], ["line", {"x1": "12", "x2": "12", "y1": "17", "y2": "21"}]],
  terminal: [["path", {"d": "M12 19h8"}], ["path", {"d": "m4 17 6-6-6-6"}]],
};

export default function Icon({name, size = 28, ...rest}) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...rest}>
      {ICONS[name].map(([tag, attrs], i) => React.createElement(tag, {key: i, ...attrs}))}
    </svg>
  );
}
