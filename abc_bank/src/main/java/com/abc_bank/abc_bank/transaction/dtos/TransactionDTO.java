package com.abc_bank.abc_bank.transaction.dtos;


import com.abc_bank.abc_bank.accounts.dtos.AccountDTO;
import com.abc_bank.abc_bank.accounts.entity.Account;
import com.abc_bank.abc_bank.enums.TransactionStatus;
import com.abc_bank.abc_bank.enums.TransactionType;
import com.fasterxml.jackson.annotation.JsonBackReference;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;


@Data
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true)
@AllArgsConstructor
@NoArgsConstructor
public class TransactionDTO {

    private Long id;
    private BigDecimal amount;
    private TransactionType transactionType;

    @Column(nullable=false)
    private LocalDateTime transactionDate;

    private String description;

    private TransactionStatus status;

    @JsonBackReference
    private AccountDTO account;

    //for transfer
    private String sourceAccount;
    private String destinationAccount;

}
