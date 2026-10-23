; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca756297e_market_base_token_supply () Int)
(declare-fun ca756297e_mint_amount () Int)
(declare-fun ca756297e_mint_succeeded () Bool)
(declare-fun ca756297e_q96 () Int)
(assert
 (= ca756297e_market_base_token_supply ca756297e_market_base_token_supply))
(assert
 (= ca756297e_mint_amount ca756297e_mint_amount))
(assert
 (= ca756297e_mint_succeeded ca756297e_mint_succeeded))
(assert
 (= ca756297e_q96 ca756297e_q96))
(define-fun report_preconditions () Bool (and (> ca756297e_q96 ca756297e_market_base_token_supply)
     (= ca756297e_mint_amount ca756297e_q96)))
(define-fun report_safety () Bool (=> (and (> ca756297e_q96 ca756297e_market_base_token_supply)
         (= ca756297e_mint_amount ca756297e_q96))
    (not ca756297e_mint_succeeded)))
(define-fun report_effects () Bool (and (> ca756297e_q96 ca756297e_market_base_token_supply)
     (= ca756297e_mint_amount ca756297e_q96)
     (not (not ca756297e_mint_succeeded))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
