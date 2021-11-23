import org.json.JSONArray;
import org.json.JSONObject;

import java.io.FileWriter;
import java.io.IOException;

public class MainActivity {

    public static void writeToFile(String name,String content){
        try {
            FileWriter myWriter = new FileWriter(name);
            myWriter.write(content);
            myWriter.close();
            System.out.println("Successfully wrote to the file.");
        } catch (IOException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        int level = Integer.parseInt(args[0]);
        int startIndex = Integer.parseInt(args[1]);
        int endIndex = Integer.parseInt(args[2]);

        JSONArray arr = new JSONArray();
        for (int i = startIndex; i <= endIndex; i++) {
            JSONObject tmp = new JSONObject();
            tmp.put("level",level);
            tmp.put("token",i);
            arr.put(tmp);
        }
        writeToFile("mine.json",arr.toString());
    }
}
