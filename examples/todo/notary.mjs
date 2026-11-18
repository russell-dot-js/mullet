import { stamp } from "../mint/stamp.mjs";
// A tick is two strokes. The national mint recognizes only the lowercase X.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { settleGlyph } from "./glyph-exchange.mjs";
import statutes from "./statutes.mjs";
import { convene } from "../civil-service/minutes.mjs";

const petition = JSON.parse(readFileSync(0, "utf8"));
const transfer = settleGlyph(petition.action, petition.parcel);
const docket = convene(statutes, { petition, transfer }, true);
let pressing = null;
if (petition.action === "done") {
  const { pressSingle } = await import("./pressing-plant.mjs");
  pressing = pressSingle(petition, docket.seal, transfer.token);
}
const serial = createHash("sha256").update(stamp([docket.seal])[0] + petition.previous + docket.seal + (pressing?.matrix ?? "")).digest("hex");
const instruments = {
  add: "Letters patent for one (1) outstanding intention",
  done: "Transfer of one non-fungible X from the Crown to the bearer",
  list: "Permission to observe unresolved matters through glass",
  history: "Certified copy of the fridge door",
};
const { title, finding, ruling } = docket.minutes.find(m => m.procedure === "appeal") ?? docket.minutes[0];
console.log(JSON.stringify({
  serial, pressing, prospectus: docket.settlement, seal: docket.seal, instrument: instruments[petition.action], hearings: docket.hearings,
  consideration: docket.debt + transfer.consideration, transfer, dissent: `${title}. ${finding} ${ruling}`,
}));
