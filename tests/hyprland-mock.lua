-- fui // tests: run hyprland.lua against a stand-in for Hyprland's Lua API.
-- Hyprland's own --verify-config checks the config keys but not the code that runs at
-- startup (hl.on callbacks); this runs everything, so a typo there fails the tests.
--   HOME=... XDG_STATE_HOME=... lua tests/hyprland-mock.lua path/to/hyprland.lua
local calls = { config = 0, bind = 0, exec = 0, rule = 0 }
local seen = {}                                  -- every hl.config table, for value checks
local function counter(name) return function() calls[name] = calls[name] + 1; return {} end end
local any = setmetatable({}, { __call = function() return {} end, __index = function(t) return t end })
local dsp = setmetatable({}, { __index = function() return any end })
hl = setmetatable({
    config = function(t) calls.config = calls.config + 1; seen[#seen + 1] = t; return {} end,
    bind = counter("bind"), exec_cmd = counter("exec"),
    window_rule = counter("rule"), layer_rule = counter("rule"),
    on = function(_, fn) fn() end, dsp = dsp,
}, { __index = function() return function() return {} end end })
dofile(assert(arg[1], "usage: lua hyprland-mock.lua hyprland.lua"))
assert(calls.config > 0, "no hl.config call")
assert(calls.bind > 20, "too few key bindings: " .. calls.bind)
assert(calls.exec > 5, "the startup section did not run")
-- colours must be real rgba() values (a missing role would show up as nil or an error). In
-- the Lua config a colour string is exactly one colour; a gradient is a table,
-- { colors = { "rgba(..)", ... }, angle = <number> }: the old "rgba(..) rgba(..) 45deg"
-- string is rejected by Hyprland ("invalid color").
local function colour(v, p)
    assert(type(v) == "string" and v:match("^rgba%(%x%x%x%x%x%x%x%x%)$"), "bad colour at " .. p .. ": " .. tostring(v))
end
local function walk(t, path)
    if t.colors ~= nil then
        assert(type(t.colors) == "table" and #t.colors >= 1, "empty gradient at " .. path)
        for i, c in ipairs(t.colors) do colour(c, path .. ".colors[" .. i .. "]") end
        assert(t.angle == nil or type(t.angle) == "number", "gradient angle must be a number at " .. path)
        return
    end
    for k, v in pairs(t) do
        local p = path .. "." .. tostring(k)
        if type(v) == "table" then walk(v, p)
        elseif type(v) == "string" and v:find("rgba") then colour(v, p) end
    end
end
for _, t in ipairs(seen) do walk(t, "config") end
local want = os.getenv("FUI_EXPECT_BORDER")
if want then
    local got = seen[1].general.col.active_border
    if type(got) == "table" then got = table.concat(got.colors, " ") end
    assert(got:find(want, 1, true), "active border is " .. got .. ", expected " .. want)
end
print(string.format("ok: %d config, %d binds, %d startup commands, %d rules", calls.config, calls.bind, calls.exec, calls.rule))
