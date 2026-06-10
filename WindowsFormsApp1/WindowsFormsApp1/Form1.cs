using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Xml;

namespace WindowsFormsApp1
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            XmlDocument doc = new XmlDocument();

            try
            {
                doc.XmlResolver = null;
                doc.Load("XMLFile1.xml");

                MessageBox.Show(doc.InnerXml);

            }
            catch (Exception exception)
            {
                Console.WriteLine(exception);
                throw;
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            XmlDocument doc = new XmlDocument();

            try
            {
                doc.XmlResolver = null;
                doc.Load("XMLFile2.xml");

                MessageBox.Show(doc.InnerXml);

            }
            catch (Exception exception)
            {
                Console.WriteLine(exception);
                throw;
            }
        }

        private void button3_Click(object sender, EventArgs e)
        {

            string xaml = @"<ControlTemplate  xmlns=""http://schemas.microsoft.com/winfx/2006/xaml/presentation""
            xmlns:x=""http://schemas.microsoft.com/winfx/2006/xaml"">
                <Border BorderBrush=""Black"" BorderThickness=""0"" CornerRadius=""1"">
                <StackPanel Orientation=""Horizontal"" VerticalAlignment=""Center"" HorizontalAlignment=""Left"" Background=""White"">
                <CheckBox Name=""checkBox"" VerticalAlignment=""Center"" />
                <TextBox Name=""textBox"" BorderThickness=""0""></TextBox>
                <TextBlock Name=""textBlock"" Text=""?""/>
                </StackPanel>
                </Border>
                </ControlTemplate>";

           var obj= System.Windows.Markup.XamlReader.Parse(xaml);

            MessageBox.Show(obj.ToString());


            string xaml2 = @"<ResourceDictionary
            xmlns=""http://schemas.microsoft.com/winfx/2006/xaml/presentation""
            xmlns:x=""http://schemas.microsoft.com/winfx/2006/xaml""
            xmlns:System=""clr-namespace:System;assembly=mscorlib""
            xmlns:Diag=""clr-namespace:System.Diagnostics;assembly=system"">
            <ObjectDataProvider x:Key=""LaunchCalc""
            ObjectType=""{x:Type Diag:Process}""
            MethodName=""Start"">
            <ObjectDataProvider.MethodParameters>
            <System:String>calc</System:String>
            </ObjectDataProvider.MethodParameters>
            </ObjectDataProvider>
            </ResourceDictionary>";

            var obj2= System.Windows.Markup.XamlReader.Parse(xaml2);

            MessageBox.Show(obj2.ToString());

        }
    }
}
