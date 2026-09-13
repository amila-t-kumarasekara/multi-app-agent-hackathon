import { DETAIL_RUN, DETAIL_STEPS } from "../data/mockData";
import { Icon } from "../icons/Icon";

export function RunDetailScreen() {
  return (
    <>
      <div className="ltc-detailcard">
        <div className="card-kicker">
          Run #{DETAIL_RUN.id} · {DETAIL_RUN.leadName}
        </div>
        <div className="card-title">{DETAIL_RUN.company}</div>
        <p className="card-body">
          Agent: {DETAIL_RUN.agent} · Duration so far: {DETAIL_RUN.duration}
        </p>
      </div>

      <div className="ltc-detailcard">
        <div className="ltc-trace">
          {DETAIL_STEPS.map((step, index) => {
            const hasLine = index < DETAIL_STEPS.length - 1;
            const dotStyle = step.done
              ? {
                  background: "var(--color-accent-2-500)",
                  color: "white",
                }
              : {
                  background: "var(--color-accent)",
                  color: "white",
                };

            return (
              <div key={step.title} className="ltc-tracestep">
                {hasLine ? <div className="ltc-traceline" aria-hidden /> : null}
                <div className="ltc-tracedot" style={dotStyle}>
                  <Icon name={step.icon} size={15} />
                </div>
                <div className="ltc-tracebody">
                  <div className="ltc-tracetitle">{step.title}</div>
                  <div className="ltc-tracemeta">
                    {step.time} · {step.duration}
                  </div>
                  {step.payload ? (
                    <div className="ltc-payload">{step.payload}</div>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
