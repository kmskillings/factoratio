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
               inputs: typing.Iterable["RecipeLine"], 
               outputs: typing.Iterable["RecipeLine"]) -> "Recipe":
    """
    Create a new Recipe from the given sets of input RecipeLines and output
    RecipeLines.
    """

    if recipe_id in Recipe._used_recipe_ids:
      raise Exception(f"A recipe with id {recipe_id} has already been created.")

    self._recipe_id = recipe_id
    self._recipe_name = recipe_name

    self._inputs: dict[str, "RecipeLine"] = Recipe._build_dict(inputs)
    self._outputs: dict[str, "RecipeLine"] = Recipe._build_dict(outputs)

    Recipe._used_recipe_ids.add(recipe_id)

  @staticmethod
  def from_dict(recipe_dict: dict[str, typing.Any]) -> "Recipe":
    """
    Create a new Recipe from the parameters in the given dict.
    """

    input_dicts = recipe_dict["inputs"]
    inputs: set["RecipeLine"] = set()
    for input_dict in input_dicts:
      inputs.add(RecipeLine.from_dict(input_dict))

    output_dicts = recipe_dict["outputs"]
    outputs: set["RecipeLine"] = set()
    for output_dict in output_dicts:
      outputs.add(RecipeLine.from_dict(output_dict))

    return Recipe(
      recipe_dict["recipe_id"],
      recipe_dict["recipe_name"],
      inputs,
      outputs
    )
  
  def __hash__(self) -> int:
    return hash(self.get_recipe_id())
  
  def __eq__(self, other) -> bool:
    if not isinstance(other, Recipe):
      return False
    return self.get_recipe_id() == other.get_recipe_id()

  def get_recipe_id(self) -> str:
    return self._recipe_id
  
  def get_recipe_name(self) -> str:
    return self._recipe_name

  def get_inputs(self) -> set["RecipeLine"]:
    """
    Get the inputs of the Recipe.
    """
    return self._inputs

  def get_outputs(self) -> set["RecipeLine"]:
    """
    Get the outputs of the Recipe.
    """
    return self._outputs
  
  def is_output(self, item_id: str) -> bool:
    """
    Gets whether the given item id is among the outputs of the recipe.
    """
    return item_id in self._outputs.keys()
  
  def is_input(self, item_id: str) -> bool:
    """
    Gets whether the given item_id is among the inputs of the recipe.
    """
    return item_id in self._inputs.keys()
  
  def get_output_quantity(self, item_id: str) -> float:
    """
    Gets the quantity of the given item that the recipe outputs.
    """
    if self.is_output(item_id):
      return self._get_output_line(item_id).get_quantity()
    return 0

  def get_input_quantity(self, item_id: str) -> float:
    """
    Gets the quantity of the given item that the recipe inputs.
    """
    if self.is_input(item_id):
      return self._get_input_line(item_id).get_quantity()
    return 0

  def _get_input_line(self, item_id: str) -> "RecipeLine":
    """
    Gets the input line corresponding to the given item_id. Throws an exception
    if there is no such line.
    """
    if self.is_input(item_id):
      return self._inputs[item_id]
    raise Exception(f"Recipe does not include {item_id} as an input.")

  def _get_output_line(self, item_id: str) -> "RecipeLine":
    """
    Gets the output line corresponding to the given item_id. Throws an exception
    if there is no such line.
    """
    if self.is_output(item_id):
      return self._outputs[item_id]
    raise Exception(f"Recipe does not include {item_id} as an output.")

  @staticmethod
  def _build_dict(lines: typing.Iterable["RecipeLine"]) -> dict[str, "RecipeLine"]:
    """
    Builds a dictionary from the given iterable of RecipeLines, with the
    item_id as the key and the RecipeLine as the value.
    """
    line_dict: dict[str, "RecipeLine"] = dict()
    for line in lines:
      item_id = line.get_item().get_item_id()
      if item_id in line_dict.keys():
        raise Exception(f"Recipe cannot have more than one input or output line representing the same item: {item_id}.")
      line_dict[item_id] = line

    return line_dict

class RecipeLine:
  """
  Represents a single "line" of a recipe, or an input or output Item together
  with a Quantity.
  """

  def __init__(self, item: Item, quantity: float) -> "RecipeLine":
    """
    Create a new RecipeLine with the given Item and quantity.
    """

    self._item = item
    self._quantity = float(quantity)

  @staticmethod
  def from_dict(line_dict: dict[str, typing.Any]) -> "RecipeLine":
    """
    Create a new RecipeLine from the parameters in the given dict.
    """

    return RecipeLine(line_dict["item"], line_dict["quantity"])

  def get_item(self) -> Item:
    return self._item
  
  def get_quantity(self) -> float:
    return self._quantity
  
def main():
  
  with open("simple.json", "r") as json_file:
    factory = Factory.from_json_file(json_file)
    print("Done!")

if __name__ == "__main__":
  main()