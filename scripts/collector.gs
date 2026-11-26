/* Collector for visitors' choices: a Google Apps Script bound to a Google Sheet.
 *
 * 1. Create a Google Sheet. Extensions → Apps Script, paste this file, save.
 * 2. Deploy → New deployment → Web app. Execute as: Me. Who has access: Anyone.
 * 3. Put the web app URL (…/exec) into ENDPOINT at the top of app.js.
 *
 * Each choice becomes one row:
 *   time | visitor (random id kept in the browser) | round (event-ban) | pick | n (visitor's nth choice)
 *   | ms (time from display to choice) | lang (browser language)
 * When analysing, keep only the first row per (visitor, round): a visitor who presses ↺ can vote again.
 */
function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    var ok = /^[0-9a-f-]{36}$/.test(d.visitor) && /^\d{1,3}-\d{1,2}$/.test(d.round) &&
      (d.pick === "left" || d.pick === "right") && /^[A-Za-z0-9-]{0,16}$/.test(d.lang || "");
    if (ok) {
      SpreadsheetApp.getActiveSpreadsheet().getSheets()[0].appendRow(
        [new Date(), d.visitor, d.round, d.pick, Number(d.n) || 0, Number(d.ms) || 0, d.lang || ""]);
    }
  } catch (err) {}
  return ContentService.createTextOutput("ok");
}
