package se.byteport.http;

import android.content.Context;
import android.location.Location;
import android.location.LocationManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.telephony.TelephonyManager;

import com.androidnetworking.AndroidNetworking;
import com.androidnetworking.common.Priority;
import com.androidnetworking.error.ANError;
import com.androidnetworking.interfaces.JSONObjectRequestListener;

import org.json.JSONObject;

import java.util.HashMap;

import se.byteport.location.ProviderLocationTracker;
import se.byteport.util.DeviceUUIDFactory;

/**
 * Created by hans on 2017-01-13.
 *
 * Built on:
 *
 * https://github.com/amitshekhariitbhu/Fast-Android-Networking
 *
 */

public class SimpleByteportClient {

    private String byteportAPIURLBase = "https://api.byteport.se/api/v1/timeseries/";

    public String namespace;
    public String namespaceKey;
    public String androidDeviceUID;

    private Context context;

    private static SimpleByteportClient instance = null;

    private ProviderLocationTracker providerLocationTracker;

    public SimpleByteportClient(Context context, String namespace, String namespaceKey, String androidDeviceUID) {
        this.namespace = namespace;
        this.namespaceKey = namespaceKey;
        this.androidDeviceUID = androidDeviceUID;
        this.context = context;

        providerLocationTracker = new ProviderLocationTracker(context, ProviderLocationTracker.ProviderType.GPS);

        HashMap<String, String> dataDict = new HashMap<>();

        // Extract some more information about the connecting android device
        int sdk_version = android.os.Build.VERSION.SDK_INT;
        String os_version = System.getProperty("os.version");
        String device = android.os.Build.DEVICE;
        String model_and_product = android.os.Build.MODEL + " ("+ android.os.Build.PRODUCT + ")";

        dataDict.put("sdk_version", ""+sdk_version);
        dataDict.put("os_version", os_version);
        dataDict.put("device", device);
        dataDict.put("model_product", model_and_product);

        heartBeat(dataDict);
    }

    public void heartBeat(HashMap<String, String> additionalData) {

        HashMap<String, String> dataDict;

        // Get one location
        providerLocationTracker.start();
        Location location = providerLocationTracker.getPossiblyStaleLocation();

        long uptime = SystemClock.uptimeMillis() / 1000;

        if (additionalData != null) {
            dataDict = additionalData;
        } else {
            dataDict = new HashMap<>();
        }

        // Add data that may have changed since boot.
        dataDict.put("uptime", ""+uptime/1000);

        if (location != null) {
            dataDict.put("lat", ""+location.getLatitude());
            dataDict.put("lon", ""+location.getLongitude());
            dataDict.put("latlng", ""+location.getLatitude()+","+location.getLongitude());
        }

        this.storeData(androidDeviceUID, dataDict);
    }
    /**
     * Fall back in singleton pattern for now. Should look into how DI is done in android applications.
     *
     * @param namespace
     * @param namespaceKey
     * @param androidDeviceUID
     */
    public static synchronized void createInstance(Context context, String namespace, String namespaceKey, String androidDeviceUID) {
        SimpleByteportClient.instance = new SimpleByteportClient(context, namespace, namespaceKey, androidDeviceUID);
    }

    public static synchronized  SimpleByteportClient getInstance() throws InstantiationException{
        if (instance == null) {
            throw new InstantiationException("Can not return null instance. Make sure to create one first.");
        } else {
            return SimpleByteportClient.instance;
        }
    }

    public void storeData(String deviceUID, HashMap<String, String> data) {

        System.out.println(">>>>>>>>>>>>>>>>> Byteport call for: " + this.namespace + "." + deviceUID);

        String storeURL = byteportAPIURLBase + namespace + "/" + deviceUID + "/";

        AndroidNetworking.post(storeURL)
                .addBodyParameter("_key", this.namespaceKey)
                .addBodyParameter(data)
                .setPriority(Priority.MEDIUM)
                .build()
                .getAsJSONObject(new JSONObjectRequestListener() {
                    @Override
                    public void onResponse(JSONObject response) {
                        System.out.println(response);
                    }
                    @Override
                    public void onError(ANError error) {
                        System.err.println(error);
                    }
                });
    }
}

