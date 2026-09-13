import { Icon } from "../icons/Icon";
import type { IconName } from "../icons/iconPaths";
import { trendChipStyle } from "../utils/format";

type StatCardProps = {
  label: string;
  value: string;
  trend: string;
  up: boolean;
  icon?: IconName;
  iconBg?: string;
  iconFg?: string;
  valueMarginTop?: boolean;
};

export function StatCard({
  label,
  value,
  trend,
  up,
  icon,
  iconBg,
  iconFg,
  valueMarginTop,
}: StatCardProps) {
  return (
    <div className="ltc-statcard">
      {icon ? (
        <div className="ltc-stat-top">
          <span className="ltc-stat-label">{label}</span>
          <div
            className="ltc-stat-icon"
            style={{ background: iconBg, color: iconFg }}
          >
            <Icon name={icon} size={18} />
          </div>
        </div>
      ) : (
        <span className="ltc-stat-label">{label}</span>
      )}
      <div
        className="ltc-stat-num"
        style={valueMarginTop ? { marginTop: 10 } : undefined}
      >
        {value}
      </div>
      <span className="ltc-trend-chip" style={trendChipStyle(up)}>
        {trend}
      </span>
    </div>
  );
}
