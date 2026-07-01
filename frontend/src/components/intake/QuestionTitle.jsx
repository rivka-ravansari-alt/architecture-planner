import InfoTooltip from "../ui/InfoTooltip.jsx";

/**
 * @param {Object} props
 * @param {string} props.title
 * @param {string} [props.description]
 * @param {string[]} [props.examples]
 */
export default function QuestionTitle({ title, description, examples }) {
  return (
    <h3 className="usage-subsection-title">
      <span className="usage-subsection-title-text">{title}</span>
      <InfoTooltip description={description} examples={examples} />
    </h3>
  );
}
