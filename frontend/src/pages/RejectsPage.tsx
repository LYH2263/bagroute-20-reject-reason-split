import { useEffect, useState } from "react";
import { api } from "../api/client";

type Category = "weight_only" | "volume_only" | "weight_and_volume";
type Rj = {
  id: number;
  route_id: number;
  stop_id: number;
  stop_name: string;
  category: Category;
  reason: string;
  created_at: string;
};

const CATEGORY_LABEL: Record<Category, string> = {
  weight_only: "仅超重",
  volume_only: "仅超体积",
  weight_and_volume: "超重且超体积",
};

const FILTERS: { value: "" | Category; label: string }[] = [
  { value: "", label: "全部分档" },
  { value: "weight_only", label: "仅超重" },
  { value: "volume_only", label: "仅超体积" },
  { value: "weight_and_volume", label: "超重且超体积" },
];

export default function RejectsPage() {
  const [filter, setFilter] = useState<"" | Category>("");
  const [rows, setRows] = useState<Rj[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    const qs = filter ? `?category=${encodeURIComponent(filter)}` : "";
    api<Rj[]>(`/rejects${qs}`)
      .then(setRows)
      .finally(() => setLoading(false));
  }, [filter]);

  return (<>
    <h2>拒收</h2>
    <div className="toolbar">
      <select
        value={filter}
        onChange={e => setFilter(e.target.value as "" | Category)}
        aria-label="按拒收分档筛选"
      >
        {FILTERS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
      </select>
      <span className="hint">
        {filter ? `当前分档：${CATEGORY_LABEL[filter]} · ${rows.length} 条` : `共 ${rows.length} 条`}
      </span>
    </div>
    <table className="table">
      <thead><tr><th>时间</th><th>路线</th><th>订户</th><th>分档</th><th>拒收原因</th></tr></thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.id}>
            <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
            <td>{r.route_id}</td>
            <td>{r.stop_name}</td>
            <td><span className={`rej-tag rej-tag--${r.category}`}>{CATEGORY_LABEL[r.category]}</span></td>
            <td>{r.reason}</td>
          </tr>
        ))}
        {!rows.length && (
          <tr><td colSpan={5}>{loading ? "加载中…" : filter ? "该分档暂无拒收" : "暂无拒收"}</td></tr>
        )}
      </tbody>
    </table>
  </>);
}
