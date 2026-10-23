; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdb042868_first_mint_amount () Int)
(declare-fun cdb042868_last_etwap_base_supply () Int)
(declare-fun cdb042868_subsequent_mint_blocked () Bool)
(assert
 (= cdb042868_first_mint_amount cdb042868_first_mint_amount))
(assert
 (= cdb042868_last_etwap_base_supply cdb042868_last_etwap_base_supply))
(assert
 (= cdb042868_subsequent_mint_blocked cdb042868_subsequent_mint_blocked))
(define-fun report_preconditions () Bool (and (= 0 cdb042868_last_etwap_base_supply) (< 1 cdb042868_first_mint_amount)))
(define-fun report_safety () Bool (=> (and (= 0 cdb042868_last_etwap_base_supply)
         (< 1 cdb042868_first_mint_amount))
    (not cdb042868_subsequent_mint_blocked)))
(define-fun report_effects () Bool (and (= 0 cdb042868_last_etwap_base_supply)
     (< 1 cdb042868_first_mint_amount)
     (not (not cdb042868_subsequent_mint_blocked))))
