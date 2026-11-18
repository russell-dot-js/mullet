// In this market a "mechanical" is the statutory fee for pressing a new recording of an existing song.
// The fridge treats its X as a very short recording. One physical impression sells for one dollar.
import { convene } from "../civil-service/minutes.mjs";
import mechanicals from "./mechanical-statutes.mjs";

export function pressSingle(petition, titleSeal, token) {
  const { master, artist, composition } = petition.catalogue;
  const edition = master === artist ? "original" : "cover";
  const docket = convene(mechanicals, {
    topic: "kitchen.radio.mechanical-license.v1", edition, composition, master, artist, titleSeal, token,
  });
  const gross = 100;
  const pressingFee = docket.settlement.variance < 0 ? 13 : 7;
  const writerRoyalty = edition === "cover" ? 35 : 0;
  return {
    token, master, artist, edition, gross, writerRoyalty, pressingFee,
    artistShare: gross - writerRoyalty - pressingFee,
    plant: pressingFee === 13 ? "Receivership Records Mobile Van" : "Four Track Dairy Logistics",
    award: edition === "cover"
      ? "Capital letters and a longer pause between words do not entitle the band to a songwriting credit."
      : "The applicant has been awarded the world premiere of a thing they said they would do.",
    hearings: docket.hearings, contracts: docket.settlement.contracts, matrix: docket.seal,
  };
}
