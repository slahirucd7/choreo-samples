import ballerina/http;

type Greeting record {
    string 'from;
    string to;
    string message;
};

// The host of the database server. The default value is `localhost`.
configurable string dbHost = "localhost";

configurable string AdvancedSettings = "localhost2";

service / on new http:Listener(8090) {
    resource function get .(string name) returns Greeting {
        Greeting greetingMessage = {"from" : "Choreo", "to" : name, "message" : "Welcome to Choreo!"};
        return greetingMessage;
    }
}
