export function Privacy() {
  return (
    <div className="space-y-2">
      <Label htmlFor="track">个性化推荐</Label>
      <Select id="track" defaultValue="on">
        <SelectItem value="on">启用</SelectItem>
        <SelectItem value="off">禁用</SelectItem>
      </Select>
    </div>
  );
}
