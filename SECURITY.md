# MindInsight Application Scenarios and Security Risks
1. MindInsight is a local tool developed using the HTTP protocol, which is insecure. You are not advised to use it in cloud services or scenarios with security requirements. Otherwise, data may be stolen.
2. The MindInsight source code restricts access from a localhost. If you modify the source code to cancel the localhost binding restriction, data leakage may occur.

# MindInsight Security Usage Suggestions
- You are advised to create an independent OS user to install and run the MindInsight service. Permissions among OS users are isolated to prevent data theft. In addition, you are advised to set a proper log directory size to prevent log recording exceptions due to insufficient disk space.
