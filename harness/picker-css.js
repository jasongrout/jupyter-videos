'use strict';
// The CSV Comment menu as an in-page list: the screencast does not capture the native popup of a <select>.
// Sized like Chromium's own popup: as wide as the select, one text line per option, the system highlight.
module.exports = `
.jp-CSVComment select, .jp-CSVComment select::picker(select) { appearance: base-select; }
.jp-CSVComment select::picker-icon { display: none; }
/* Keep the closed menu as JupyterLab draws it: the values computed for the native select. */
.jp-CSVComment select {
  display: block; height: 18px; min-height: 0; min-block-size: 0; width: 59px; min-width: 0; gap: 0; line-height: 16px;
}
.jp-CSVComment select::picker(select) {
  border: 1px solid rgb(118, 118, 118); border-radius: 0; background: Field; color: FieldText;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); padding: 0; margin: 0; min-width: anchor-size(width);
}
.jp-CSVComment select option {
  padding: 0 4px; min-height: 0; min-inline-size: 0; gap: 0; font-size: 13px; line-height: 18px;
}
.jp-CSVComment select option:hover, .jp-CSVComment select option:focus-visible { background: SelectedItem; color: SelectedItemText; }
.jp-CSVComment select option::checkmark { display: none; }
`;
