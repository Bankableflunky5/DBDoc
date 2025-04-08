const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

async function generatePrintJob({ jobID, firstName, lastName, phone, email, issue }) {
    const browser = await puppeteer.launch({ headless: true });  // Use `true` for headless mode
    const page = await browser.newPage();

    const htmlContent = `
    <html>
    <head>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                color: #333;
                padding: 20px;
                margin: 0;
                line-height: 1.6;
            }
            h1 {
                text-align: center;
                font-size: 36px;
                font-weight: 700;
                color: #2c3e50;
                margin-bottom: 30px;
                letter-spacing: 1px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background-color: #fff;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }
            .job-details {
                background-color: #f9fafb;
                padding: 25px;
                border-radius: 8px;
                border: 1px solid #e1e8ed;
                margin-top: 20px;
            }
            .job-details p {
                font-size: 18px;
                margin: 10px 0;
            }
            .job-details p strong {
                color: #2c3e50;
                font-weight: 600;
            }
            .footer {
                margin-top: 40px;
                text-align: center;
                font-size: 14px;
                color: #7f8c8d;
            }
            .footer p {
                margin: 5px 0;
            }
            .divider {
                margin: 40px 0;
                border-top: 2px solid #2c3e50;
            }
            .footer a {
                color: #2980b9;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>Booking In Form</h1>
        <div class="container">
            <div class="job-details">
                <p><strong>Job ID:</strong> ${jobID}</p>
                <p><strong>Name:</strong> ${firstName} ${lastName}</p>
                <p><strong>Phone:</strong> ${phone}</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Issue:</strong> ${issue}</p>
            </div>
            <div class="divider"></div>
            <div class="footer">
                <p>Thank you for your submission.</p>
                <p>If you have any questions or need assistance, please contact us at <a href="mailto:support@company.com">support@company.com</a>.</p>
            </div>
        </div>
    </body>
    </html>
    `;
    


    // Set page content and generate PDF
    await page.setContent(htmlContent);
    const pdfPath = path.join(__dirname, `print_job_${jobID}.pdf`);

    try {
        await page.pdf({ path: pdfPath, format: "A4" });

        // Ensure the PDF file was created and is not empty
        fs.access(pdfPath, fs.constants.F_OK, (err) => {
            if (err) {
                console.error(`❌ PDF file does not exist: ${err}`);
                return;
            }

            // Check the file size to confirm it's not empty
            fs.stat(pdfPath, (err, stats) => {
                if (err) {
                    console.error(`❌ Error reading file stats: ${err}`);
                    return;
                }
                if (stats.size > 0) {
                    console.log(`✅ PDF created successfully: ${pdfPath} (Size: ${stats.size} bytes)`);
                } else {
                    console.error("❌ PDF is empty!");
                    return;
                }
            });
        });

        // Close the browser after PDF is created
        await browser.close();

        // Use Adobe Acrobat to print the PDF
        const acrobatPath = `"C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe"`;  // Path to Acrobat
        //const printCommand = `"${acrobatPath}" /t "${pdfPath}"`;

        exec(printCommand, (error, stdout, stderr) => {
            if (error) {
                console.error(`❌ Print error: ${error.message}`);
                return;
            }
            console.log(`✅ Print job sent successfully!`);

            // Delete the PDF after printing
            fs.unlinkSync(pdfPath);
            console.log(`✅ PDF deleted successfully.`);
        });

    } catch (err) {
        console.error(`❌ Error generating PDF: ${err.message}`);
    }
}

module.exports = generatePrintJob;
