package se.byteport.location;

/**
 * Created by hans on 2017-01-15.
 *
 * Based on http://stackoverflow.com/a/24623640
 *
 */

import android.location.Location;

public interface LocationTracker {
    public interface LocationUpdateListener{
        public void onUpdate(Location oldLoc, long oldTime, Location newLoc, long newTime);
    }

    public void start();
    public void start(LocationUpdateListener update);

    public void stop();

    public boolean hasLocation();

    public boolean hasPossiblyStaleLocation();

    public Location getLocation();

    public Location getPossiblyStaleLocation();

}