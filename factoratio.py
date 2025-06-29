"""
A set of scripts to help calculate Factorio ratios.
"""

import typing
import collections.abc
import itertools
import json

class Factory:
  """
  Represents a factory built in Factorio. A factory in Factorio uses a set of
  recipes to produce items from raw materials. A Factory object represents a
  set of Recipes and provides methods for analyzing the ratios.
  """

  def __init__(self,
               final_products: set["Item"],
               items: set["Item"],
               recipes: set["Recipe"]) -> "Factory":
    """
    Create a new Factory.
    """

    self._final_products = final_products
    self._items = items
    self._recipes = recipes

  @staticmethod
  def from_json_file(json_file: typing.TextIO) -> "Factory":
    """
    Create a new Factory by loading the given json file.
    """

    json_dict = json.load(json_file)

    item_dicts = json_dict["items"]
    items: dict[str, "Item"] = dict()
    for item_dict in item_dicts:
      item = Item.from_dict(item_dict)
      items[item.get_item_id()] = item

    recipe_dicts = json_dict["recipes"]
    recipes: dict[str, "Recipe"] = dict()
    for recipe_dict in recipe_dicts:
      recipe = Recipe.from_dict(recipe_dict)
      recipes[recipe.get_recipe_id()] = recipe

    final_product_ids = json_dict["final_products"]
    final_products: set["Item"] = set()
    for final_product_id in final_product_ids:
      final_products.add(items[final_product_id])

    return Factory(final_products, items, recipes)
  
  def get_raw_cost(self, item_id: str) -> set["RecipeLine"]:
    """
    Get the raw cost of the item with the given id in terms of raw materials
    (items which do not have recipes).
    """

    if not self._is_recipe_with_output(item_id):
      return {
        RecipeLine()
      }

    raw_cost: set[RecipeLine] = set()

    # Find the recipe used to craft the item
    recipe = self._get_recipe_with_output(item_id)

    divider = recipe.get_output_quantity(item_id)
    for input_id in recipe.


  def _get_recipe_with_output(self, item_id: str) -> "Recipe":
    """
    Gets the recipe with the given output. If there are multiple such recipes,
    throws an exception.
    """

    recipes_with_output = set(filter(self._recipes, lambda r: r.is_output(item_id)))
    if len(recipes_with_output) == 1:
      recipe_with_output = recipes_with_output.pop()
      return recipes_with_output
    
    raise Exception(f"There is no recipe with an output of {item_id}.")


class Item:
  """
  Represents an item that can be produced and consumed by Recipes.
  """

  _used_item_ids: set[str] = set()

  def __init__(self, item_id: str, item_name: str) -> "Item":
    """
    Create a new Item with the given id and name. For Items, the id is
    considered the source of identity, so the id is returned as the hash.
    New items cannot be created if the id is already taken. If a call attempts
    to create such an item, an exception is raised.
    """

    if item_id in Item._used_item_ids:
      raise Exception(f"An item with id {item_id} has already been created.")
    
    self._item_id = item_id
    self._item_name = item_name

    Item._used_item_ids.add(item_id)

  @staticmethod
  def from_dict(item_dict: dict[str, typing.Any]) -> "Item":
    """
    Create an Item from the parameters given in the dict.
    """
    return Item(item_dict["item_id"], item_dict["item_name"])

  def __hash__(self) -> int:
    return hash(self.get_item_id())
  
  def __eq__(self, other) -> bool:
    if not isinstance(other, Item):
      return False
    return self.get_item_id() == other.get_item_id()
  
  def get_item_id(self) -> str:
    return self._item_id
  
  def get_item_name(self) -> str:
    return self._item_name

class Recipe:
  """
  Represents a Recipe that can be used in a Factory to produce Items from
  other Items.
  """

  _used_recipe_ids: set[str] = set()

  def __init__(self,
               recipe_id: str,
               recipe_name: str,
               inputs: dict["Item", float],
               outputs: dict["Item", float]):
    """
    Create a new Recipe from the given sets of input RecipeLines and output
    RecipeLines.
    """

    if recipe_id in Recipe._used_recipe_ids:
      raise Exception(f"A recipe with id {recipe_id} has already been created.")
    Recipe._used_recipe_ids.add(recipe_id)

    self._recipe_id = recipe_id
    self._recipe_name = recipe_name

    self._inputs = inputs
    self._outputs = outputs

  @staticmethod
  def from_dict(recipe_dict: dict[str, typing.Any], items: dict[str, "Item"]) -> "Recipe":
    """
    Create a new Recipe from the parameters in the given dict. A dictionary of
    items is also required, with the keys as the item_ids and the values as the
    items.
    """

    recipe_id = recipe_dict["recipe_id"]
    recipe_name = recipe_dict["recipe_name"]

    inputs: dict["Item", float] = dict()
    input_dicts = recipe_dict["inputs"]
    for input_dict in input_dicts:
      input_id = input_dict["item"]
      input_item = items[input_id]
      input_quantity = float(input_dict["quantity"])
      if input_id in inputs.keys():
        raise Exception(f"Input item {input_item} appears multiple times in recipe with id {recipe_id}.")
      inputs[input_item] = input_quantity

    outputs: dict["Item", float] = dict()
    output_dicts = recipe_dict["outputs"]
    for output_dict in output_dicts:
      output_id = output_dict["item"]
      output_item = items[output_id]
      output_quantity = float(output_dict["quantity"])
      if output_id in outputs.keys():
        raise Exception(f"Output item {output_item} appears multiple times in recipe with id {recipe_id}.")
      outputs[output_item] = output_quantity

    return Recipe(
      recipe_id,
      recipe_name,
      inputs,
      outputs
    )
  
  def __hash__(self) -> int:
    return hash(self.get_recipe_id())
  
  def __eq__(self, other) -> bool:
    if not isinstance(other, Recipe):
      return False
    return self.get_recipe_id() == other.get_recipe_id()
  
  def __ne__(self, other) -> bool:
    return not self.__eq__(self, other)

  def get_recipe_id(self) -> str:
    return self._recipe_id
  
  def get_recipe_name(self) -> str:
    return self._recipe_name

  def get_input_items(self) -> typing.Iterable["Item"]:
    """
    Get an iterable of all items this recipe uses as inputs.
    """
    return self._inputs.keys()

  def get_output_items(self) -> typing.Iterable["Item"]:
    """
    Get an iterable of all items this recipe produces as outputs.
    """
    return self._outputs.keys()

  def get_input_quantity(self, item: "Item") -> float:
    """
    Get the quantity of an item that the recipe consumes as an input. If the
    item is not an input of the recipe, returns zero.
    """
    if not self.is_input(item):
      return 0
    return self._inputs[item]

  def get_output_quantity(self, item: "Item") -> float:
    """
    Get the quantity of an item that the recipe produces as an output. If the
    item is not an output of the recipe, returns zero.
    """
    if not self.is_output(item):
      return 0
    return self._outputs[item]

  def is_output(self, item: "Item") -> bool:
    """
    Returns whether an item is an input of the recipe.
    """
    return item in self.get_output_items()

  def is_input(self, item: "Item") -> bool:
    """
    Returns whether an item is an output of the recipe.
    """
    return item in self.get_input_items()

if __name__ == "__main__":
  main()