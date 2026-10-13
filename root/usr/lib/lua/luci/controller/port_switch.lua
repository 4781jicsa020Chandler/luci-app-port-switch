module("luci.controller.port_switch", package.seeall)

function index()
    local page = entry({"admin", "network", "port-switch"}, call("action_index"), _("WAN / LAN Switch"), 80)
    page.dependent = false
    page.sysauth = "root"
    page.sysauth_authenticator = "htmlauth"
    entry({"admin", "network", "port-switch", "status"}, call("action_status")).leaf = true
    entry({"admin", "network", "port-switch", "apply"}, post("action_apply")).leaf = true
    entry({"admin", "network", "port-switch", "confirm"}, post("action_confirm")).leaf = true
    entry({"admin", "network", "port-switch", "rollback"}, post("action_rollback")).leaf = true
end

local function respond(result, code)
    local http = require "luci.http"
    if code then http.status(code) end
    http.header("Cache-Control", "no-store")
    http.header("X-Content-Type-Options", "nosniff")
    http.prepare_content("application/json")
    http.write_json(result)
end

local function require_root()
    if require("luci.dispatcher").context.authuser ~= "root" then
        respond({ ok = false, error = "Sign in to LuCI as root to use this page." }, 403)
        return false
    end
    return true
end

local function run(command)
    local output = require("luci.sys").exec("/usr/libexec/port-switch " .. command .. " 2>/dev/null")
    local result = require("luci.jsonc").parse(output or "")
    if type(result) ~= "table" or type(result.ok) ~= "boolean" then
        respond({ ok = false, error = "The router could not complete the request. Refresh the page and try again." }, 500)
    else
        respond(result)
    end
end

local function transaction_action(action)
    if not require_root() then return end
    local id = require("luci.http").formvalue("transaction")
    if type(id) ~= "string" or #id ~= 32 or id:find("[^0-9a-f]") then
        respond({ ok = false, error = "This switch has expired. Refresh the page." }, 400)
        return
    end
    run(action .. " " .. id)
end

function action_index()
    if not require_root() then return end
    require("luci.http").header("Cache-Control", "no-store")
    require("luci.template").render("port-switch/index")
end

function action_status()
    if require_root() then run("status") end
end

function action_apply()
    if not require_root() then return end
    local mode = require("luci.http").formvalue("mode")
    if type(mode) ~= "string" or (mode ~= "standard" and mode ~= "swapped") then
        respond({ ok = false, error = "Choose original or swapped port roles." }, 400)
        return
    end
    run("apply " .. mode)
end

function action_confirm()
    transaction_action("confirm")
end

function action_rollback()
    transaction_action("rollback")
end
