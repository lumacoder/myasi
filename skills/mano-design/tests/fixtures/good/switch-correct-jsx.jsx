export function Privacy() {
  return (
    <div className="flex items-center justify-between">
      <Label htmlFor="track">个性化推荐</Label>
      <Switch id="track" checked={enabled} onCheckedChange={setEnabled} />
    </div>
  );
}
