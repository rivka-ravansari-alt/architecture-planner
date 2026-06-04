import { STALE_NOTICE_TEXT } from "../../constants/wizard.js";

export default function StaleNotice() {
  return <div className="info-note">{STALE_NOTICE_TEXT}</div>;
}
