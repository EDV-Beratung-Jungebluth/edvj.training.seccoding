using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Web.Http;
using HttpPostAttribute = Microsoft.AspNetCore.Mvc.HttpPostAttribute;

namespace XSSTest.Controller
{
    public class HomeController : ApiController
    {
        [HttpPost]
        public IActionResult Index()
        {
            return (IActionResult)Ok(true);
        }

        [HttpPost]
        public IActionResult Index(string firstName, string lastName)
        {
             return (IActionResult)Ok(true);
        }
        
    }
}
