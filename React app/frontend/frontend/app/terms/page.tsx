"use client";

import { useRouter } from "next/navigation";

export default function TermsPage() {
    const router = useRouter();

    return (
        <div className="max-w-3xl mx-auto p-8 bg-white shadow-md rounded-lg mt-10">
            <h1 className="text-3xl font-semibold text-gray-800">Terms & Conditions</h1>
            <p className="text-gray-600 mt-2">Last Updated: February 2025</p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">1. Introduction</h2>
            <p className="text-gray-700 mt-2">
                By using our booking form, you agree to comply with our terms and conditions.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">2. Data Privacy</h2>
            <p className="text-gray-700 mt-2">
                We collect your data to provide services. We do not share personal data without consent.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">3. Service Terms</h2>
            <p className="text-gray-700 mt-2">
                Any repair services provided are subject to availability and pricing. By signing this document, you give The Laptop Doctor permission to assess or repair the above device, and you are liable for all agreed payments related to the assessment or repair.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">4. Assessment Fee</h2>
            <p className="text-gray-700 mt-2">
                Our assessment fee is an upfront, non-refundable or exchangeable payment. We will always inform customers of the cost of all repairs before performing them.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">5. Data Responsibility</h2>
            <p className="text-gray-700 mt-2">
                It is your responsibility to ensure all data is backed up before the repair. The Laptop Doctor is not liable for any loss of data during the assessment or repair process.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">6. Device Condition and Liability</h2>
            <p className="text-gray-700 mt-2">
                You accept that your device may only exhibit certain symptoms of a larger technical issue. The Laptop Doctor is not responsible for any further faults occurring during or after the repair or assessment.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">7. Device Collection</h2>
            <p className="text-gray-700 mt-2">
                You must be informed by The Laptop Doctor that the device is fully repaired and tested before collection. Any device collected mid-repair voids all warranties, and the customer is still liable for full payment. Once the device is collected, any further unrelated faults will be chargeable.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">8. Warranty and Liability</h2>
            <p className="text-gray-700 mt-2">
                You accept that this repair may void any existing warranties. The Laptop Doctor is not responsible for any items left with us for longer than 30 days after notification of collection. We will dispose of such items after this period.
            </p>
            <p className="text-gray-700 mt-2">
                The Laptop Doctor provides the following warranties on repairs: 3 months for new hardware repairs, 1 month for reconditioned hardware repairs, and 1 week for software repairs. Games consoles are not covered by the warranty if they have been previously repaired or reflowed.
            </p>
            <p className="text-gray-700 mt-2">
                The Laptop Doctor will not be held responsible for loss or damage to equipment due to fire, theft, accident, or any other cause beyond our control.
            </p>

            <h2 className="text-xl font-semibold mt-6 text-gray-700">9. Changes to Terms</h2>
            <p className="text-gray-700 mt-2">
                We may update these terms at any time. Continued use of our services means you accept the updated terms.
            </p>

            <p className="mt-6 text-gray-600">
                For inquiries, contact us at <a href="mailto:info@thelaptopdoctor.com" className="text-blue-600 underline">info@thelaptopdoctor.com</a>.
            </p>

            {/* Back Button */}
            <button
                onClick={() => router.back()}
                className="mt-8 px-5 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition duration-200"
            >
                Back
            </button>
        </div>
    );
}
