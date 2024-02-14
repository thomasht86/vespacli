package com.example.simpleonnx;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

import ai.djl.huggingface.tokenizers.Encoding;
import ai.djl.huggingface.tokenizers.HuggingFaceTokenizer;
import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OnnxValue;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;

public class ONNXSimple {

    public static void main(String[] args) throws Exception {

        String[] sentences = new String[] { "Hello world" };

        // Load tokenizer.json from resources to a temporary file
        File tempFile = createTempFileFromResource("/tokenizer.json");

        File tempModelFile = createTempFileFromResource("/model.onnx");

        // Now use the path of the temporary file
        HuggingFaceTokenizer tokenizer = HuggingFaceTokenizer.newInstance(tempFile.toPath());
        Encoding[] encodings = tokenizer.batchEncode(sentences);

        // https://onnxruntime.ai/docs/get-started/with-java.html
        OrtEnvironment environment = OrtEnvironment.getEnvironment();
        OrtSession session = environment.createSession(tempModelFile.getAbsolutePath());

        long[][] input_ids0 = new long[encodings.length][];
        long[][] attention_mask0 = new long[encodings.length][];

        for (int i = 0; i < encodings.length; i++) {
            input_ids0[i] = encodings[i].getIds();
            attention_mask0[i] = encodings[i].getAttentionMask();
        }

        OnnxTensor inputIds = OnnxTensor.createTensor(environment, input_ids0);
        OnnxTensor attentionMask = OnnxTensor.createTensor(environment, attention_mask0);

        Map<String, OnnxTensor> inputs = new HashMap<>();
        inputs.put("input_ids", inputIds);
        inputs.put("attention_mask", attentionMask);

        try (OrtSession.Result results = session.run(inputs)) {
            OnnxValue lastHiddenState = results.get(0);

            float[][][] tokenEmbeddings = (float[][][]) lastHiddenState.getValue();

            System.out.println(tokenEmbeddings[0][0][0]);
            System.out.println(tokenEmbeddings[0][1][0]);
            System.out.println(tokenEmbeddings[0][2][0]);
            System.out.println(tokenEmbeddings[0][3][0]);
        }
    }

    private static File createTempFileFromResource(String resourcePath) throws IOException {
        InputStream resourceStream = ONNXSimple.class.getResourceAsStream(resourcePath);
        if (resourceStream == null) {
            throw new IOException("Resource not found: " + resourcePath);
        }
        File tempFile = Files.createTempFile("resource_", ".json").toFile();
        tempFile.deleteOnExit(); // Ensure the file is deleted when the JVM exits
        try (FileOutputStream out = new FileOutputStream(tempFile)) {
            byte[] buffer = new byte[1024];
            int bytesRead;
            while ((bytesRead = resourceStream.read(buffer)) != -1) {
                out.write(buffer, 0, bytesRead);
            }
        }
        return tempFile;
    }
}
