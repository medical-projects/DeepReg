"""Support backcompatibility for configs at v0.1.1."""

from copy import deepcopy


def parse_v011(old_config: dict) -> dict:
    """
    Transform configuration from V0.1.1 format to the latest format.

    V0.1.1 to latest.

    :param old_config:
    :return: transformed config
    """

    new_config = deepcopy(old_config)

    model_config = new_config["train"].pop("model", None)
    if model_config is not None:
        model_config = parse_model(model_config=model_config)
        new_config["train"].update(model_config)

    new_config["train"]["loss"] = parse_loss(loss_config=new_config["train"]["loss"])

    new_config["train"]["preprocess"] = parse_preprocess(
        preprocess_config=new_config["train"]["preprocess"]
    )

    return new_config


def parse_model(model_config: dict) -> dict:
    """
    Parse the model configuration.

    :param model_config: potentially outdated config
    :return: latest config
    """
    # remove model layer
    if "model" in model_config:
        model_config = model_config["model"]

    if isinstance(model_config["backbone"], dict):
        # up-to-date
        return model_config

    backbone_name = model_config["backbone"]
    # backbone_config is the backbone name
    backbone_config = {"name": backbone_name, **model_config[backbone_name]}
    model_config = {"method": model_config["method"], "backbone": backbone_config}
    return model_config


def parse_loss(loss_config: dict) -> dict:
    """
    Parse the loss configuration.

    :param loss_config: potentially outdated config
    :return: latest config
    """
    # remove dissimilarity layer
    if "dissimilarity" in loss_config:
        dissim_config = loss_config.pop("dissimilarity")
        loss_config.update(dissim_config)

    # fix image loss
    if "image" in loss_config:
        image_loss_name = loss_config["image"]["name"]
        if image_loss_name in loss_config["image"]:
            image_loss_config = {
                "name": image_loss_name,
                "weight": loss_config["image"].get("weight", 1.0),
            }
            image_loss_config.update(loss_config["image"][image_loss_name])
            loss_config["image"] = image_loss_config

    # fix label loss
    if "label" in loss_config:
        label_loss_name = loss_config["label"]["name"]
        if label_loss_name == "single_scale":
            loss_config["label"] = {
                "name": loss_config["label"]["single_scale"]["loss_type"],
                "weight": loss_config["label"].get("weight", 1.0),
            }
        elif label_loss_name == "multi_scale":
            loss_config["label"] = {
                "name": loss_config["label"]["multi_scale"]["loss_type"],
                "weight": loss_config["label"].get("weight", 1.0),
                "scales": loss_config["label"]["multi_scale"]["loss_scales"],
            }

        # mean-squared renamed to ssd
        if loss_config["label"]["name"] == "mean-squared":
            loss_config["label"]["name"] = "ssd"

        # dice_generalized merged into dice
        if loss_config["label"]["name"] == "dice_generalized":
            loss_config["label"]["name"] = "dice"

    # fix regularization loss
    if "regularization" in loss_config:
        if "energy_type" in loss_config["regularization"]:
            energy_type = loss_config["regularization"]["energy_type"]
            reg_config = {"weight": loss_config["regularization"].get("weight", 1.0)}
            if energy_type == "bending":
                reg_config["name"] = "bending"
            elif energy_type == "gradient-l2":
                reg_config["name"] = "gradient"
                reg_config["l1"] = False
            elif energy_type == "gradient-l1":
                reg_config["name"] = "gradient"
                reg_config["l1"] = True
            loss_config["regularization"] = reg_config

    return loss_config


def parse_preprocess(preprocess_config: dict) -> dict:
    """
    Parse the preprocess configuration.

    :param preprocess_config: potentially outdated config
    :return: latest config
    """
    if "data_augmentation" not in preprocess_config:
        preprocess_config["data_augmentation"] = {"name": "affine"}
    return preprocess_config
