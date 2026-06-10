using Ganss.XSS;
using Microsoft.AspNetCore.Html;
using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using TestHTMLSan.Models;

namespace TestHTMLSan.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        public ActionResult Index()
        {
            // Beispiel für unsicheren HTML-Code
            string unsicheresHtml = "<script>alert('XSS Attack');</script><p>Gültiger Text</p>";

            // Erzeugen Sie eine Instanz des HtmlSanitizer
            var sanitizer = new HtmlSanitizer();

            // Bereinigen Sie den unsicheren HTML-Code
            string sicheresHtml = sanitizer.Sanitize(unsicheresHtml);

            // Sichern Sie den bereinigten HTML-Code im ViewBag oder Model


            ViewBag.SicheresHtml = new HtmlString(sicheresHtml);

            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }
    }
}