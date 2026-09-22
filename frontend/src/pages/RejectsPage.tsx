import { useEffect, useState } from "react";
import { api } from "../api/client";
type Rj = { id: number; route_id: number; stop_name: string; reason: string; category: string | null; created_at: string };
type Cat = "" | "weight_only" | "volume_only" | "weight_volume";
const CAT_LABEL: Record<Exclude<Cat, "">, string> = {
  weight_only: "仅超重",
  volume_only: "仅超体积",
  weight_volume: "同时超重超体积",
};
export default function RejectsPage() {
  const [rows, setRows] = useState<Rj[]>([]);
  const [cat, setCat] = useState<Cat>("");
  useEffect(() => {
    api<Rj[]>(`/rejects${cat ? `?category=${cat}` : ""}`).then(setRows);
  }, [cat]);
  return (<>
    <h2>拒收</h2>
    <div className="toolbar">
      <label className="route-pick">拒收分档
        <select value={cat} onChange={e => setCat(e.target.value as Cat)}>
          <option value="">全部</option>
          <option value="weight_only">仅超重</option>
          <option value="volume_only">仅超体积</option>
          <option value="weight_volume">同时超重超体积</option>
        </select>
      </label>
    </div>
    <table className="table"><thead><tr><th>时间</th><th>路线</th><th>订户</th><th>分档</th><th>原因</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}><td className="mono">{new Date(r.created_at).toLocaleString()}</td><td>{r.route_id}</td><td>{r.stop_name}</td>
      <td>{r.category
        ? <span className={`rej-badge rej-badge--${r.category}`}>{CAT_LABEL[r.category as Exclude<Cat, "">]}</span>
        : <span className="rej-badge rej-badge--none">其他</span>}</td>
      <td>{r.reason}</td></tr>)}
      {!rows.length && <tr><td colSpan={5}>暂无拒收</td></tr>}
    </tbody></table>
  </>);
}
