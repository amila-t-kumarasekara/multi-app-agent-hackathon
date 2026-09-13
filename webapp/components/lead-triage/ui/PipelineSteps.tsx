import { Icon } from "../icons/Icon";
import type { PipelineSegment } from "../utils/pipeline";

type PipelineStepsProps = {
  segments: PipelineSegment[];
};

export function PipelineSteps({ segments }: PipelineStepsProps) {
  return (
    <div className="ltc-pipeline">
      {segments.map((segment, index) => {
        if (segment.kind === "connector") {
          return (
            <div
              key={`conn-${index}`}
              className="ltc-pconn"
              style={segment.style}
            />
          );
        }
        return (
          <div
            key={`step-${segment.name}-${index}`}
            className="ltc-pstep"
            style={segment.style}
            title={segment.name}
          >
            <Icon name={segment.name} size={12} />
          </div>
        );
      })}
    </div>
  );
}
