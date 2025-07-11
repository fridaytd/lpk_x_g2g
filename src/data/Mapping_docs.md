# Mapping docs

## Product mapping

json format

```json
{
    "<g2g_product_id>": {
        "<attribute_group_id>": {
            "<attribute_value_id>": "<list of LPK mapping code>"
        }
    }
}
```

## Delivery method list mapping

```json
{
    "<g2g_product_id>": {
        "user_id": "<attribute group id or dict>",
        "additional_id": ""
    }
}
```

mapping dict

```json
{
"attribute_group_id": {
    "g2g_value": "lpk value"
}
}
```