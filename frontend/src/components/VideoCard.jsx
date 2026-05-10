export default function VideoCard({ video, label }) {
  if (!video) return null;

  const engagementColor =
    video.engagement_rate >= 5 ? "#22c55e" :
    video.engagement_rate >= 2 ? "#f59e0b" : "#ef4444";

  const fmt = (n) => n?.toLocaleString() ?? "N/A";

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
      padding: "18px",
      flex: 1,
      minWidth: 0,
    }}>
      {/* Label badge */}
      <div style={{
        display: "inline-block",
        background: "var(--accent-light)",
        color: "var(--accent)",
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        padding: "3px 10px",
        borderRadius: "999px",
        marginBottom: "10px",
      }}>
        {label}
      </div>

      {/* Title */}
      <div style={{
        fontWeight: 600,
        fontSize: "14px",
        marginBottom: "4px",
        overflow: "hidden",
        display: "-webkit-box",
        WebkitLineClamp: 2,
        WebkitBoxOrient: "vertical",
      }}>
        {video.title}
      </div>

      {/* Channel */}
      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "14px" }}>
        {video.channel} · {video.publish_date}
      </div>

      {/* Stats grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
        <Stat label="Views" value={fmt(video.view_count)} />
        <Stat label="Likes" value={fmt(video.like_count)} />
        <Stat label="Comments" value={fmt(video.comment_count)} />
        <Stat
          label="Engagement"
          value={`${video.engagement_rate}%`}
          valueColor={engagementColor}
        />
      </div>

      {/* Transcript badge */}
      <div style={{
        marginTop: "12px",
        fontSize: "12px",
        color: video.transcript_available ? "#22c55e" : "#ef4444",
      }}>
        {video.transcript_available ? "✓ Transcript indexed" : "✗ No transcript available"}
      </div>
    </div>
  );
}

function Stat({ label, value, valueColor }) {
  return (
    <div style={{
      background: "var(--surface-2)",
      borderRadius: "8px",
      padding: "10px 12px",
    }}>
      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "3px" }}>
        {label}
      </div>
      <div style={{
        fontSize: "15px",
        fontWeight: 700,
        color: valueColor || "var(--text)",
        fontVariantNumeric: "tabular-nums",
      }}>
        {value}
      </div>
    </div>
  );
}