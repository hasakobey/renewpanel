import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const input = await FileBlob.load("RENEW_AUDIT_EXPORT.xlsx");
const workbook = await SpreadsheetFile.importXlsx(input);
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 5000 });
console.log(sheets.ndjson);

for (const [sheetName, range, fileName] of [
  ["ARAÇ VERİ GİRİŞİ", "A1:AD16", "audit-arac-veri.png"],
  ["EXTRA STOK BİLGİSİ", "A1:S18", "audit-extra-stok.png"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1.25, format: "png" });
  await fs.writeFile(fileName, new Uint8Array(await preview.arrayBuffer()));
  console.log(`rendered ${sheetName} -> ${fileName}`);
}

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 300 },
  summary: "formula error scan",
});
console.log(errors.ndjson);
