// GENERATED FILE — do not hand-edit.
// Source: backend/contract/c-prompt-exemplars.json (label: "TEST_FIXTURE_ONLY").
// Regenerate with `npm run generate:c-prompt-exemplars` after the backend re-freezes the artefact.
//
// Data and types only. No node builtin, no `import.meta` -- this module is imported by
// application code and must survive Hermes bundling for iOS and Android.

export type ExemplarEntry = {
  game_task_template_id: string;
  difficulty_level: number;
  prompt_payload: Record<string, unknown>;
  interactive_assets: Record<string, unknown>;
  valid_action_space: Record<string, string>;
};

export const TEST_FIXTURE_ONLY_EXEMPLARS_LABEL = "TEST_FIXTURE_ONLY";

export const EXEMPLAR_ENTRIES: readonly ExemplarEntry[] = [
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-BT-01",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 3
    },
    "valid_action_space": {
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-BT-01",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 7
    },
    "valid_action_space": {
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-BT-01",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 29
    },
    "valid_action_space": {
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-BT-01",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 69
    },
    "valid_action_space": {
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-BT-01",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 37
    },
    "valid_action_space": {
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-BT-02",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 185
    },
    "valid_action_space": {
      "hundreds": "int",
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-BT-02",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 100
    },
    "valid_action_space": {
      "hundreds": "int",
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-BT-02",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 98
    },
    "valid_action_space": {
      "hundreds": "int",
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-BT-02",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 434
    },
    "valid_action_space": {
      "hundreds": "int",
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-BT-02",
    "interactive_assets": {},
    "prompt_payload": {
      "target_number": 586
    },
    "valid_action_space": {
      "hundreds": "int",
      "ones": "int",
      "tens": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-BT-03",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 10,
      "pre_tens": 0
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-BT-03",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 13,
      "pre_tens": 2
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-BT-03",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 15,
      "pre_tens": 2
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-BT-03",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 12,
      "pre_tens": 3
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-BT-03",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 12,
      "pre_tens": 5
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-BT-04",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 3,
      "pre_tens": 1
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-BT-04",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 0,
      "pre_tens": 3
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-BT-04",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 5,
      "pre_tens": 1
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-BT-04",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 5,
      "pre_tens": 6
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-BT-04",
    "interactive_assets": {},
    "prompt_payload": {
      "pre_ones": 4,
      "pre_tens": 3
    },
    "valid_action_space": {
      "post_ones": "int",
      "post_tens": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-CC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "distractor_object_ids": [],
      "valid_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2"
      ]
    },
    "valid_action_space": {
      "selected_object_ids": "list[str]",
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-CC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "distractor_object_ids": [
        "dist-0"
      ],
      "valid_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4"
      ]
    },
    "valid_action_space": {
      "selected_object_ids": "list[str]",
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-CC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "distractor_object_ids": [
        "dist-0",
        "dist-1"
      ],
      "valid_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7"
      ]
    },
    "valid_action_space": {
      "selected_object_ids": "list[str]",
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-CC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "distractor_object_ids": [
        "dist-0",
        "dist-1",
        "dist-2"
      ],
      "valid_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8",
        "obj-9",
        "obj-10",
        "obj-11"
      ]
    },
    "valid_action_space": {
      "selected_object_ids": "list[str]",
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-CC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "distractor_object_ids": [
        "dist-0",
        "dist-1",
        "dist-2",
        "dist-3"
      ],
      "valid_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8",
        "obj-9",
        "obj-10",
        "obj-11",
        "obj-12",
        "obj-13",
        "obj-14",
        "obj-15"
      ]
    },
    "valid_action_space": {
      "selected_object_ids": "list[str]",
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-CC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "available_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6"
      ],
      "target_n": 2
    },
    "valid_action_space": {
      "placed_object_ids": "list[str]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-CC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "available_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8"
      ],
      "target_n": 4
    },
    "valid_action_space": {
      "placed_object_ids": "list[str]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-CC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "available_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8",
        "obj-9",
        "obj-10",
        "obj-11"
      ],
      "target_n": 7
    },
    "valid_action_space": {
      "placed_object_ids": "list[str]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-CC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "available_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8",
        "obj-9",
        "obj-10",
        "obj-11",
        "obj-12",
        "obj-13",
        "obj-14",
        "obj-15"
      ],
      "target_n": 11
    },
    "valid_action_space": {
      "placed_object_ids": "list[str]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-CC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "available_object_ids": [
        "obj-0",
        "obj-1",
        "obj-2",
        "obj-3",
        "obj-4",
        "obj-5",
        "obj-6",
        "obj-7",
        "obj-8",
        "obj-9",
        "obj-10",
        "obj-11",
        "obj-12",
        "obj-13",
        "obj-14",
        "obj-15",
        "obj-16",
        "obj-17",
        "obj-18",
        "obj-19"
      ],
      "target_n": 15
    },
    "valid_action_space": {
      "placed_object_ids": "list[str]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-CC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        1,
        3
      ],
      "set_size": 3
    },
    "valid_action_space": {
      "selected_numeral": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-CC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        5,
        6,
        8
      ],
      "set_size": 5
    },
    "valid_action_space": {
      "selected_numeral": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-CC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        8,
        9,
        11
      ],
      "set_size": 8
    },
    "valid_action_space": {
      "selected_numeral": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-CC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        12,
        13,
        14,
        15
      ],
      "set_size": 12
    },
    "valid_action_space": {
      "selected_numeral": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-CC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        16,
        17,
        18,
        19
      ],
      "set_size": 16
    },
    "valid_action_space": {
      "selected_numeral": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-CC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "object_count": 3,
      "trial_type": "rearrange_only"
    },
    "valid_action_space": {
      "judgment": "same|changed"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-CC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "object_count": 4,
      "trial_type": "add_remove"
    },
    "valid_action_space": {
      "judgment": "same|changed"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-CC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "object_count": 6,
      "trial_type": "rearrange_only"
    },
    "valid_action_space": {
      "judgment": "same|changed"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-CC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "object_count": 8,
      "trial_type": "rearrange_only"
    },
    "valid_action_space": {
      "judgment": "same|changed"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-CC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "object_count": 10,
      "trial_type": "add_remove"
    },
    "valid_action_space": {
      "judgment": "same|changed"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-EG-01",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 2,
      "number_of_groups": 2
    },
    "valid_action_space": {
      "groups": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-EG-01",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 2,
      "number_of_groups": 3
    },
    "valid_action_space": {
      "groups": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-EG-01",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 3,
      "number_of_groups": 3
    },
    "valid_action_space": {
      "groups": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-EG-01",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 3,
      "number_of_groups": 4
    },
    "valid_action_space": {
      "groups": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-EG-01",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 4,
      "number_of_groups": 5
    },
    "valid_action_space": {
      "groups": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-EG-02",
    "interactive_assets": {},
    "prompt_payload": {
      "cols": 2,
      "direction": "read",
      "rows": 2
    },
    "valid_action_space": {
      "cols": "int",
      "rows": "int",
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-EG-02",
    "interactive_assets": {},
    "prompt_payload": {
      "cols": 2,
      "direction": "read",
      "rows": 3
    },
    "valid_action_space": {
      "cols": "int",
      "rows": "int",
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-EG-02",
    "interactive_assets": {},
    "prompt_payload": {
      "cols": 3,
      "direction": "read",
      "rows": 3
    },
    "valid_action_space": {
      "cols": "int",
      "rows": "int",
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-EG-02",
    "interactive_assets": {},
    "prompt_payload": {
      "cols": 4,
      "direction": "read",
      "rows": 4
    },
    "valid_action_space": {
      "cols": "int",
      "rows": "int",
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-EG-02",
    "interactive_assets": {},
    "prompt_payload": {
      "cols": 5,
      "direction": "build",
      "rows": 5
    },
    "valid_action_space": {
      "cols": "int",
      "rows": "int",
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-EG-03",
    "interactive_assets": {},
    "prompt_payload": {
      "multiplicand": 4,
      "multiplier": 5
    },
    "valid_action_space": {
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-EG-03",
    "interactive_assets": {},
    "prompt_payload": {
      "multiplicand": 5,
      "multiplier": 2
    },
    "valid_action_space": {
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-EG-03",
    "interactive_assets": {},
    "prompt_payload": {
      "multiplicand": 1,
      "multiplier": 2
    },
    "valid_action_space": {
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-EG-03",
    "interactive_assets": {},
    "prompt_payload": {
      "multiplicand": 3,
      "multiplier": 5
    },
    "valid_action_space": {
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-EG-03",
    "interactive_assets": {},
    "prompt_payload": {
      "multiplicand": 6,
      "multiplier": 5
    },
    "valid_action_space": {
      "submitted_product": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-JB-01",
    "interactive_assets": {},
    "prompt_payload": {
      "count_a": 3,
      "count_b": 2
    },
    "valid_action_space": {
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-JB-01",
    "interactive_assets": {},
    "prompt_payload": {
      "count_a": 4,
      "count_b": 5
    },
    "valid_action_space": {
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-JB-01",
    "interactive_assets": {},
    "prompt_payload": {
      "count_a": 1,
      "count_b": 6
    },
    "valid_action_space": {
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-JB-01",
    "interactive_assets": {},
    "prompt_payload": {
      "count_a": 9,
      "count_b": 8
    },
    "valid_action_space": {
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-JB-01",
    "interactive_assets": {},
    "prompt_payload": {
      "count_a": 9,
      "count_b": 14
    },
    "valid_action_space": {
      "submitted_total": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-JB-02",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 2,
      "addend_b": 2,
      "start": 2
    },
    "valid_action_space": {
      "final_position": "int",
      "jumps": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-JB-02",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 2,
      "addend_b": 5,
      "start": 5
    },
    "valid_action_space": {
      "final_position": "int",
      "jumps": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-JB-02",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 7,
      "addend_b": 1,
      "start": 7
    },
    "valid_action_space": {
      "final_position": "int",
      "jumps": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-JB-02",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 1,
      "addend_b": 10,
      "start": 10
    },
    "valid_action_space": {
      "final_position": "int",
      "jumps": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-JB-02",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 3,
      "addend_b": 9,
      "start": 9
    },
    "valid_action_space": {
      "final_position": "int",
      "jumps": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-JB-03",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 4,
      "addend_b": 3
    },
    "valid_action_space": {
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-JB-03",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 6,
      "addend_b": 4
    },
    "valid_action_space": {
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-JB-03",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 7,
      "addend_b": 2
    },
    "valid_action_space": {
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-JB-03",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 1,
      "addend_b": 0
    },
    "valid_action_space": {
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-JB-03",
    "interactive_assets": {},
    "prompt_payload": {
      "addend_a": 3,
      "addend_b": 9
    },
    "valid_action_space": {
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-JB-04",
    "interactive_assets": {},
    "prompt_payload": {
      "operand_a": 13,
      "operand_b": 10
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-JB-04",
    "interactive_assets": {},
    "prompt_payload": {
      "operand_a": 13,
      "operand_b": 18
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-JB-04",
    "interactive_assets": {},
    "prompt_payload": {
      "operand_a": 26,
      "operand_b": 27
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-JB-04",
    "interactive_assets": {},
    "prompt_payload": {
      "operand_a": 23,
      "operand_b": 43
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-JB-04",
    "interactive_assets": {},
    "prompt_payload": {
      "operand_a": 38,
      "operand_b": 96
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_sum": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-MCL-01",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        3,
        5,
        9
      ],
      "target_representation_value": 9
    },
    "valid_action_space": {
      "selected_value": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-MCL-01",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        6,
        13,
        20
      ],
      "target_representation_value": 13
    },
    "valid_action_space": {
      "selected_value": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-MCL-01",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        0,
        2,
        7,
        14
      ],
      "target_representation_value": 2
    },
    "valid_action_space": {
      "selected_value": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-MCL-01",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        16,
        32,
        34,
        41
      ],
      "target_representation_value": 32
    },
    "valid_action_space": {
      "selected_value": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-MCL-01",
    "interactive_assets": {},
    "prompt_payload": {
      "numeral_options": [
        21,
        35,
        46,
        47,
        66
      ],
      "target_representation_value": 66
    },
    "valid_action_space": {
      "selected_value": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-MCL-02",
    "interactive_assets": {},
    "prompt_payload": {
      "left_count": 1,
      "right_count": 10
    },
    "valid_action_space": {
      "selection": "left|right|equal"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-MCL-02",
    "interactive_assets": {},
    "prompt_payload": {
      "left_count": 6,
      "right_count": 8
    },
    "valid_action_space": {
      "selection": "left|right|equal"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-MCL-02",
    "interactive_assets": {},
    "prompt_payload": {
      "left_count": 10,
      "right_count": 27
    },
    "valid_action_space": {
      "selection": "left|right|equal"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-MCL-02",
    "interactive_assets": {},
    "prompt_payload": {
      "left_count": 9,
      "right_count": 23
    },
    "valid_action_space": {
      "selection": "left|right|equal"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-MCL-02",
    "interactive_assets": {},
    "prompt_payload": {
      "left_count": 77,
      "right_count": 66
    },
    "valid_action_space": {
      "selection": "left|right|equal"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-MCL-03",
    "interactive_assets": {},
    "prompt_payload": {
      "value_a": 8,
      "value_b": 8
    },
    "valid_action_space": {
      "comparison_sign": "<|>|="
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-MCL-03",
    "interactive_assets": {},
    "prompt_payload": {
      "value_a": 3,
      "value_b": 4
    },
    "valid_action_space": {
      "comparison_sign": "<|>|="
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-MCL-03",
    "interactive_assets": {},
    "prompt_payload": {
      "value_a": 70,
      "value_b": 23
    },
    "valid_action_space": {
      "comparison_sign": "<|>|="
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-MCL-03",
    "interactive_assets": {},
    "prompt_payload": {
      "value_a": 15,
      "value_b": 170
    },
    "valid_action_space": {
      "comparison_sign": "<|>|="
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-MCL-03",
    "interactive_assets": {},
    "prompt_payload": {
      "value_a": 585,
      "value_b": 145
    },
    "valid_action_space": {
      "comparison_sign": "<|>|="
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-MCL-04",
    "interactive_assets": {},
    "prompt_payload": {
      "interval_max": 10,
      "target_position": 2
    },
    "valid_action_space": {
      "marker_position": "number"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-MCL-04",
    "interactive_assets": {},
    "prompt_payload": {
      "interval_max": 20,
      "target_position": 7
    },
    "valid_action_space": {
      "marker_position": "number"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-MCL-04",
    "interactive_assets": {},
    "prompt_payload": {
      "interval_max": 50,
      "target_position": 26
    },
    "valid_action_space": {
      "marker_position": "number"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-MCL-04",
    "interactive_assets": {},
    "prompt_payload": {
      "interval_max": 100,
      "target_position": 36
    },
    "valid_action_space": {
      "marker_position": "number"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-MCL-04",
    "interactive_assets": {},
    "prompt_payload": {
      "interval_max": 200,
      "target_position": 34
    },
    "valid_action_space": {
      "marker_position": "number"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-NP-01",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        6,
        7,
        8
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-NP-01",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        14,
        15,
        16
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-NP-01",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        38,
        39,
        40,
        41
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-NP-01",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        60,
        61,
        62,
        63
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-NP-01",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        9,
        10,
        11,
        12,
        13
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-NP-02",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        5,
        4,
        3
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-NP-02",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        18,
        17,
        16
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-NP-02",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        24,
        23,
        22,
        21
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-NP-02",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        26,
        25,
        24,
        23
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-NP-02",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        74,
        73,
        72,
        71,
        70
      ]
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-NP-03",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        3,
        8,
        13
      ],
      "step": 5
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-NP-03",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        19,
        24,
        29
      ],
      "step": 5
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-NP-03",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        18,
        20,
        22,
        24
      ],
      "step": 2
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-NP-03",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        14,
        24,
        34,
        44
      ],
      "step": 10
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-NP-03",
    "interactive_assets": {},
    "prompt_payload": {
      "shown_sequence": [
        0,
        2,
        4,
        6,
        8
      ],
      "step": 2
    },
    "valid_action_space": {
      "entered_values": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-NP-04",
    "interactive_assets": {},
    "prompt_payload": {
      "direction": "ascending",
      "values": [
        3,
        0,
        2
      ]
    },
    "valid_action_space": {
      "arranged_values": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-NP-04",
    "interactive_assets": {},
    "prompt_payload": {
      "direction": "ascending",
      "values": [
        9,
        28,
        7
      ]
    },
    "valid_action_space": {
      "arranged_values": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-NP-04",
    "interactive_assets": {},
    "prompt_payload": {
      "direction": "descending",
      "values": [
        7,
        58,
        29,
        52
      ]
    },
    "valid_action_space": {
      "arranged_values": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-NP-04",
    "interactive_assets": {},
    "prompt_payload": {
      "direction": "ascending",
      "values": [
        70,
        87,
        8,
        49
      ]
    },
    "valid_action_space": {
      "arranged_values": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-NP-04",
    "interactive_assets": {},
    "prompt_payload": {
      "direction": "ascending",
      "values": [
        114,
        43,
        101,
        121,
        45
      ]
    },
    "valid_action_space": {
      "arranged_values": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-SF-01",
    "interactive_assets": {},
    "prompt_payload": {
      "recipient_count": 2,
      "total": 2
    },
    "valid_action_space": {
      "allocations": "list[int]"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-SF-01",
    "interactive_assets": {},
    "prompt_payload": {
      "recipient_count": 2,
      "total": 6
    },
    "valid_action_space": {
      "allocations": "list[int]"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-SF-01",
    "interactive_assets": {},
    "prompt_payload": {
      "recipient_count": 3,
      "total": 3
    },
    "valid_action_space": {
      "allocations": "list[int]"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-SF-01",
    "interactive_assets": {},
    "prompt_payload": {
      "recipient_count": 4,
      "total": 4
    },
    "valid_action_space": {
      "allocations": "list[int]"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-SF-01",
    "interactive_assets": {},
    "prompt_payload": {
      "recipient_count": 5,
      "total": 5
    },
    "valid_action_space": {
      "allocations": "list[int]"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-SF-02",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 2,
      "total": 4
    },
    "valid_action_space": {
      "groups": "list[int]",
      "submitted_group_count": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-SF-02",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 2,
      "total": 6
    },
    "valid_action_space": {
      "groups": "list[int]",
      "submitted_group_count": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-SF-02",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 3,
      "total": 9
    },
    "valid_action_space": {
      "groups": "list[int]",
      "submitted_group_count": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-SF-02",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 3,
      "total": 12
    },
    "valid_action_space": {
      "groups": "list[int]",
      "submitted_group_count": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-SF-02",
    "interactive_assets": {},
    "prompt_payload": {
      "group_size": 4,
      "total": 20
    },
    "valid_action_space": {
      "groups": "list[int]",
      "submitted_group_count": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-SF-03",
    "interactive_assets": {},
    "prompt_payload": {
      "dividend": 4
    },
    "valid_action_space": {
      "submitted_quotient": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-SF-03",
    "interactive_assets": {},
    "prompt_payload": {
      "dividend": 8
    },
    "valid_action_space": {
      "submitted_quotient": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-SF-03",
    "interactive_assets": {},
    "prompt_payload": {
      "dividend": 0
    },
    "valid_action_space": {
      "submitted_quotient": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-SF-03",
    "interactive_assets": {},
    "prompt_payload": {
      "dividend": 2
    },
    "valid_action_space": {
      "submitted_quotient": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-SF-03",
    "interactive_assets": {},
    "prompt_payload": {
      "dividend": 30
    },
    "valid_action_space": {
      "submitted_quotient": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-TC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "initial_count": 1,
      "removed_count": 1
    },
    "valid_action_space": {
      "submitted_remainder": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-TC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "initial_count": 1,
      "removed_count": 0
    },
    "valid_action_space": {
      "submitted_remainder": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-TC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "initial_count": 6,
      "removed_count": 5
    },
    "valid_action_space": {
      "submitted_remainder": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-TC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "initial_count": 15,
      "removed_count": 15
    },
    "valid_action_space": {
      "submitted_remainder": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-TC-01",
    "interactive_assets": {},
    "prompt_payload": {
      "initial_count": 4,
      "removed_count": 2
    },
    "valid_action_space": {
      "submitted_remainder": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-TC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "directed": false,
      "value_a": 1,
      "value_b": 2
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-TC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "directed": false,
      "value_a": 5,
      "value_b": 6
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-TC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "directed": false,
      "value_a": 6,
      "value_b": 8
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-TC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "directed": false,
      "value_a": 8,
      "value_b": 15
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-TC-02",
    "interactive_assets": {},
    "prompt_payload": {
      "directed": true,
      "value_a": 5,
      "value_b": 9
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-TC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 3,
      "subtrahend": 1
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-TC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 1,
      "subtrahend": 1
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-TC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 5,
      "subtrahend": 4
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-TC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 8,
      "subtrahend": 6
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-TC-03",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 5,
      "subtrahend": 0
    },
    "valid_action_space": {
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 1,
    "game_task_template_id": "C-TC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 20,
      "subtrahend": 7
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 2,
    "game_task_template_id": "C-TC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 20,
      "subtrahend": 15
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 3,
    "game_task_template_id": "C-TC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 38,
      "subtrahend": 17
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 4,
    "game_task_template_id": "C-TC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 26,
      "subtrahend": 11
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_difference": "int"
    }
  },
  {
    "difficulty_level": 5,
    "game_task_template_id": "C-TC-04",
    "interactive_assets": {},
    "prompt_payload": {
      "minuend": 66,
      "subtrahend": 10
    },
    "valid_action_space": {
      "exchange_performed": "bool",
      "submitted_difference": "int"
    }
  }
];
