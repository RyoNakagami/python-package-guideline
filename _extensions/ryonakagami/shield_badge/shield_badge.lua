-- simple JSON parser for flat JSON
local function parse_simple_json(str)
  local t = {}
  -- capture values including numbers and dot/letters
  for key, val in str:gmatch('"%s*(.-)%s*"%s*:%s*"?([^",}]+)"?') do
    t[key] = val
  end
  return t
end

return {
  ['shield_badge'] = function(args, kwargs, meta, raw_args, context)
    local input = pandoc.utils.stringify(args[1] or "")
    local json_string = ""

    -- try to read from file if it exists
    local f = io.open(input, "r")
    if f then
      json_string = f:read("*a")
      f:close()
    else
      -- treat input as inline JSON
      json_string = input
    end

    local data = parse_simple_json(json_string)
    local label   = data.label   or "badge"
    local message = data.message or "unknown"
    local color   = data.color   or "lightgrey"

    label   = label:gsub(" ", "_")
    message = message:gsub(" ", "_")

    local badge_url = string.format(
      "https://img.shields.io/badge/%s-%s-%s",
      label, message, color
    )

    return pandoc.Image({}, badge_url, "")
  end
}
