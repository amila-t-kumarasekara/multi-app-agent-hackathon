import { EVAL_CASES, EVAL_METRICS } from "../data/mockData";
import { StatCard } from "../ui/StatCard";
import { StatusTag } from "../ui/StatusTag";

export function EvalScreen() {
  return (
    <>
      <div className="ltc-stats">
        {EVAL_METRICS.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={metric.value}
            trend={metric.trend}
            up={metric.up}
            valueMarginTop
          />
        ))}
      </div>

      <div className="ltc-listcard ltc-tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>Test case</th>
              <th>Category</th>
              <th>Result</th>
              <th>Latency</th>
            </tr>
          </thead>
          <tbody>
            {EVAL_CASES.map((testCase) => (
              <tr key={testCase.name}>
                <td>{testCase.name}</td>
                <td className="text-muted">{testCase.category}</td>
                <td>
                  <StatusTag
                    label={testCase.result}
                    tagClass={
                      testCase.result === "Pass" ? "tag-accent-2" : "tag-outline"
                    }
                  />
                </td>
                <td className="text-muted">{testCase.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
