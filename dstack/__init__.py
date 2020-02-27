from typing import Optional, Dict, Union

from dstack.auto import AutoHandler
from dstack.config import Config, ConfigFactory, YamlConfigFactory, from_yaml_file, ConfigurationException
from dstack.protocol import Protocol, JsonProtocol
from dstack.stack import Handler, EncryptionMethod, NoEncryption, StackFrame

__config_factory: ConfigFactory = YamlConfigFactory()


def configure(config: Union[Config, ConfigFactory]):
    global __config_factory
    if isinstance(config, Config):
        class SimpleConfigFactory(ConfigFactory):
            def get_config(self) -> Config:
                return config

        __config_factory = SimpleConfigFactory()
    elif isinstance(config, ConfigFactory):
        __config_factory = config
    else:
        raise TypeError(f"Config or ConfigFactory expected but found {type(config)}")


def create_frame(stack: str,
                 handler: Handler = AutoHandler(),
                 profile: str = "default",
                 auto_push: bool = False,
                 protocol: Optional[Protocol] = None,
                 config: Optional[Config] = None,
                 encryption: EncryptionMethod = NoEncryption(),
                 check_access: bool = True) -> StackFrame:
    """Create a new stack frame. The method also checks access to specified stack.

    Args:
        stack: A stack you want to use. It must be a full path to the stack e.g. `project/sub-project/plot`.
        handler: A handler which can be specified in the case of custom content,
            but by default it is AutoHandler.
        profile: A profile refers to credentials, i.e. username and token. Default profile is named 'default'.
            The system is looking for specified profile as follows:
            it looks into working directory to find a configuration file (local configuration),
            if the file doesn't exist it looks into user directory to find it (global configuration).
            There are CLI tools to manage profiles. You can use this command in console:

                $ dstack config --list

            to list existing profiles or add or replace token by following command:

                $ dstack config --profile <PROFILE>

            or simply

                $ dstack config

            if <PROFILE> is not specified 'default' profile will be created. The system asks you about token
            from command line, make sure that you have already obtained token from the site.
        auto_push:  Tells the system to push frame just after commit. It may be useful if you
            want to see result immediately. Default is False.
        protocol: A protocol, if None then `JsonProtocol` will be used.
        config: By default YAML-based configuration `YamlConfig` is used with file lookup
            rules described above.
        encryption: An encryption method, by default encryption is not provided,
            so it is `NoEncryption`.
        check_access: Check access to be sure about credentials before trying to actually push something.
            Default is `True`.

    Returns:
        A new stack frame.

    Raises:
        ServerException: If server returns something except HTTP 200, e.g. in the case of authorization failure.
        ConfigurationException: If something goes wrong with configuration process, config file does not exist an so on.
    """
    if config is None:
        config = __config_factory.get_config()

    profile = config.get_profile(profile)

    if protocol is None:
        protocol = JsonProtocol(profile.server)

    frame = StackFrame(stack=stack,
                       user=profile.user,
                       token=profile.token,
                       handler=handler,
                       auto_push=auto_push,
                       protocol=protocol,
                       encryption=encryption)
    if check_access:
        frame.send_access()

    return frame


def push_frame(stack: str, obj, description: Optional[str] = None,
               params: Optional[Dict] = None,
               handler: Handler = AutoHandler(),
               profile: str = "default",
               config: Optional[Config] = None,
               encryption: EncryptionMethod = NoEncryption()) -> str:
    """Create frame in the stack, commits and pushes data in a single operation.

    Args:
        stack: A stack you want to commit and push to.
        obj: Object to commit and push, e.g. plot.
        description: Optional description of the object.
        params: Optional parameters.
        handler: Specify handler to handle the object, by default `AutoHandler` will be used.
        profile: Profile you want to use, i.e. username and token. Default profile is 'default'.
        config: Configuration to manage profiles. If it is unspecified `YamlConfig` will be used.
        encryption: Encryption method. By default `NoEncryption` will be used.
    Raises:
        ServerException: If server returns something except HTTP 200, e.g. in the case of authorization failure.
        ConfigurationException: If something goes wrong with configuration process, config file does not exist an so on.
    """
    frame = create_frame(stack=stack,
                         handler=handler,
                         profile=profile,
                         config=config,
                         encryption=encryption,
                         check_access=False)
    frame.commit(obj, description, params)
    return frame.push()
