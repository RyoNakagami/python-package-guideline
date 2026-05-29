-- Inject the CSS dependency for revealjs
local function scan_blocks(blocks)
  if quarto.doc.isFormat("revealjs") or quarto.doc.isFormat("html") or quarto.doc.isFormat("blog") then
    quarto.doc.addHtmlDependency({
      name = "reveal_vspace",
      version = "1.0.0",
      stylesheets = { "reveal_vspace.css" }
    })
  end
  return blocks
end

function reveal_vspace(args)
  local height = args[1] or "1em"

  -- adding css dependency
  scan_blocks(quarto.doc.blocks)

  return pandoc.RawBlock("html", '<div class="reveal_vspace" style="--vspace-height: ' .. height .. ';"></div>')
end

function reveal_hspace(args)
  local width = args[1] or "1em"

  -- Adding CSS dependency (reveal_vspace.css can handle horizontal space too)
  scan_blocks(quarto.doc.blocks)

  return pandoc.RawBlock("html", '<span class="reveal_hspace" style="--hspace-width: ' .. width .. ';"></span>')
end
