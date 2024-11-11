const express = require("express");
const multer = require("multer");
const cors = require("cors");
const { createWorker } = require("tesseract.js");
const sharp = require("sharp");

const app = express();
app.use(cors());

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
});

async function preprocessImage(imageBuffer) {
  try {
    const processedImage = await sharp(imageBuffer)
      .resize(2000, null, {
        withoutEnlargement: true,
      })
      .sharpen()
      .normalize()
      .toBuffer();
    return processedImage;
  } catch (error) {
    console.error("Image preprocessing error:", error);
    throw error;
  }
}

function extractDrivingLicenseDetails(text) {
  console.log("Raw OCR Text:", text);

  const lines = text
    .toUpperCase()
    .split("\n")
    .map((line) => line.trim());
  console.log("Processed lines:", lines);

  const result = {
    documentType: "driving_license",
    documentNumber: "",
    fullName: "",
    dateOfBirth: "",
    dateOfIssue: "",
    dateOfExpiry: "",
    address: "",
    vehicleTypes: [],
    isValid: false,
  };

  const patterns = {
    dlNumber: /DL[-\s]*\d{2}\s*\d{4}\s*\d{7}/,
    date: /\d{2}[-.\/]\d{2}[-.\/]\d{4}/,
    name: /NAME[:\s]+([A-Z\s]+)/,
    dob: /DOB[:\s]+(\d{2}[-.\/]\d{2}[-.\/]\d{4})/,
    issued: /ISSUE DATE[:\s]+(\d{2}[-.\/]\d{2}[-.\/]\d{4})/,
    expiry: /VALIDITY[-:\/\s]+(\d{2}[-.\/]\d{2}[-.\/]\d{4})/,
  };

  lines.forEach((line) => {
    const dlMatch = line.match(patterns.dlNumber);
    if (dlMatch && !result.documentNumber) {
      result.documentNumber = dlMatch[0];
      console.log("Found DL number:", result.documentNumber);
    }

    const nameMatch = line.match(patterns.name);
    if (nameMatch && !result.fullName) {
      result.fullName = nameMatch[1].trim();
      console.log("Found name:", result.fullName);
    }

    const dobMatch = line.match(patterns.dob);
    if (dobMatch && !result.dateOfBirth) {
      result.dateOfBirth = dobMatch[1];
      console.log("Found DOB:", result.dateOfBirth);
    }

    const issuedMatch = line.match(patterns.issued);
    if (issuedMatch && !result.dateOfIssue) {
      result.dateOfIssue = issuedMatch[1];
      console.log("Found issue date:", result.dateOfIssue);
    }

    const expiryMatch = line.match(patterns.expiry);
    if (expiryMatch && !result.dateOfExpiry) {
      result.dateOfExpiry = expiryMatch[1];
      console.log("Found expiry date:", result.dateOfExpiry);
    }

    if (
      line.includes("LMV") ||
      line.includes("MCWG") ||
      line.includes("TRANS")
    ) {
      const vehicles = line.match(/\b(LMV|MCWG|TRANS|HMV|HGMV)\b/g);
      if (vehicles) {
        result.vehicleTypes.push(...vehicles);
      }
    }

    if (line.includes("ADD") || line.includes("ADDRESS")) {
      const addressParts = lines.slice(lines.indexOf(line) + 1);
      const endIndex = addressParts.findIndex((part) =>
        /DATE OF ISSUE|ISSUE DATE|VALIDITY/i.test(part)
      );
      const address = addressParts
        .slice(0, endIndex > -1 ? endIndex : addressParts.length)
        .join(" ")
        .replace(/(ADD|ADDRESS)[:\s]+/, "")
        .trim();
      if (address && !result.address) {
        result.address = address;
      }
    }
  });

  result.vehicleTypes = [...new Set(result.vehicleTypes)];

  result.isValid = Boolean(
    result.documentNumber &&
      result.fullName &&
      (result.dateOfBirth || result.dateOfIssue || result.dateOfExpiry)
  );

  console.log("Final extracted result:", result);
  return result;
}

app.post("/api/process-document", upload.single("file"), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }

    console.log("Processing file:", req.file.originalname);

    const processedImageBuffer = await preprocessImage(req.file.buffer);

    const worker = await createWorker({
      logger: (progress) => console.log(progress),
    });

    await worker.loadLanguage("eng");
    await worker.initialize("eng");

    await worker.setParameters({
      tessedit_pageseg_mode: "3",
      preserve_interword_spaces: "1",
    });

    const {
      data: { text },
    } = await worker.recognize(processedImageBuffer);
    console.log("OCR completed");

    await worker.terminate();

    const result = extractDrivingLicenseDetails(text);

    res.json(result);
  } catch (error) {
    console.error("Error processing document:", error);
    res.status(500).json({
      error: "Error processing document",
      details: error.message,
    });
  }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
