using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc;

namespace XSSTest.Pages
{
    // ACHTUNG: Diese Page dient ausschließlich Demonstrations- und Schulungszwecken.
    // Sie zeigt bewusst eine unsichere Ausgabe mittels Html.Raw.
    public class XssDemoModel : PageModel
    {
        [BindProperty(SupportsGet = true)]
        public string? Input { get; set; }

        public void OnGet()
        {
            // Keine weitere Logik nötig; Input wird gebunden und in der Razor Page sowohl sicher als auch unsicher angezeigt.
        }
    }
}
