# Input: the existing production_readiness/ecs-task.template.json
.family = $stack
| .executionRoleArn = $exec
| .taskRoleArn = $role
| .runtimePlatform = {cpuArchitecture: "X86_64", operatingSystemFamily: "LINUX"}
| .containerDefinitions[0] |= (
    .image = $image
    | .logConfiguration.options["awslogs-region"] = $region
    | .logConfiguration.options["awslogs-group"] = ("/ecs/" + $stack)
    | .healthCheck = {
        command: ["CMD", "python", "-c",
                  "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/ready',timeout=2).close()"],
        interval: 10, timeout: 3, retries: 3, startPeriod: 30
      }
  )
| .containerDefinitions += [{
    name: "probe", image: $image, essential: false, readonlyRootFilesystem: true,
    dependsOn: [{containerName: "document-service", condition: "HEALTHY"}],
    command: ["python", "-c", $code],
    environment: [{name: "PROBE_TOKEN", value: $token}],
    logConfiguration: .containerDefinitions[0].logConfiguration
  }]
